import csv
import logging
from dataclasses import dataclass, field
from typing import List, Dict
from Generator import Generator
from Job import Job


@dataclass
class CSVSource:
    """
    Each CSV file is configured via a CSVSource:
      - nickname: a short name for debugging/logging.
      - file_path: path to the CSV file.
      - fraction: fraction of the total jobs to generate from this file.

    The CSV file must in AzurePublicDataset format and have a header:
      TIMESTAMP,ContextTokens,GeneratedTokens

    The TIMESTAMP column is ignored after our Feb 20 meeting.
    ContextTokens is used as the Job's init_size, and
    GeneratedTokens is used as the Job's expected_output.
    """
    nickname: str
    file_path: str
    fraction: float  # Fraction of the total jobs to generate from this source (e.g., 0.7, 0.3)
    # Internal fields
    rows: List[Dict] = field(default_factory=list)
    target_count: int = 0  # Number of jobs to generate from this source
    current_index: int = 0  # Pointer to the next row to use

    def load_rows(self):
        """Load CSV rows from file using DictReader."""
        try:
            with open(self.file_path, newline="") as f:
                reader = csv.DictReader(f)
                self.rows = list(reader)
        except Exception as e:
            logging.error(f"Failed to read CSV file {self.file_path}: {e}")
            raise


class CSVGenerator(Generator):
    """
    Generator that creates new Jobs based on multiple CSV files.

    The total number of jobs to generate is provided by the user.
    The loader will generate jobs from multiple CSV sources sequentially until its fraction is exhausted.
    For each CSV source, the target number of jobs is computed from its fraction (with the last source
    receiving the remainder).
    """

    def __init__(self, env, scheduler, speed, total, dropout, csv_sources: List[CSVSource]):
        super().__init__(env, scheduler, speed, total, dropout, name="MultiCSV Generator")
        self.csv_sources = csv_sources

        # Check that the sum of fractions is 1.
        sum_fractions = sum(src.fraction for src in self.csv_sources)
        if abs(sum_fractions - 1.0) > 1e-6:
            raise ValueError(f"Fractions of CSV sources do not sum to 1 (got {sum_fractions})")

        # Load CSV rows for each source.
        for source in self.csv_sources:
            source.load_rows()

        # Compute target count for each CSV source based on its fraction.
        accumulated = 0
        num_src = len(self.csv_sources)
        for i, src in enumerate(self.csv_sources):
            if i < num_src - 1:
                src.target_count = int(self.total_limit * src.fraction)
                accumulated += src.target_count
            else:
                # For the last source, assign the remainder.
                src.target_count = self.total_limit - accumulated

        # Check each source has enough rows.
        for src in self.csv_sources:
            if len(src.rows) < src.target_count:
                raise ValueError(
                    f"CSV source '{src.nickname}' does not have enough rows "
                    f"(target {src.target_count} but available {len(src.rows)})"
                )

        # Report data source combinations
        logging.debug(f"Loaded {len(self.csv_sources)} CSV sources:")
        for i, src in enumerate(self.csv_sources):
            logging.debug(f"[{i+1}] {src.nickname}: {src.target_count} jobs from {src.file_path} (total {len(src.rows)} rows)")


    def __current_source(self) -> CSVSource|None:
        """
        Return the current CSV source that has not yet generated all its jobs.
        If all sources are done, return None.
        """
        for source in self.csv_sources:
            if source.current_index < source.target_count:
                return source
        return None


    def try_add_one_job(self) -> bool:
        """
        Try to add one job from one of the CSV sources.
        It selects the first CSV source that has not yet generated its target number of jobs.
        Returns True if successful, False otherwise.
        """
        # Find the first CSV source that still has jobs to generate.
        selected_source = self.__current_source()

        # Read the next row from the selected CSV source.
        row = selected_source.rows[selected_source.current_index]
        selected_source.current_index += 1

        try:
            init_size = int(row["ContextTokens"])
            expected_output = int(row["GeneratedTokens"])
        except Exception as e:
            logging.error(f"Error parsing CSV row in source '{selected_source.nickname}': {e}")
            return False

        arrival_time = self.env.now
        job = Job(job_id=self.job_id,
                  arrival_time=arrival_time,
                  init_size=init_size,
                  expected_output=expected_output)
        if self.scheduler.receive_job(job):
            logging.debug(f"Loader >> Loaded job {self.job_id} [{init_size}/{expected_output}] from source '{selected_source.nickname}'")
            return True
        return False


    def __str__(self):
        base_str = super().__str__()
        sources_info = " | ".join([
            f"{src.nickname}: {src.current_index}/{src.target_count}"
            for src in self.csv_sources
        ])
        return f"{base_str}\tSources: {sources_info}"
