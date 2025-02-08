class Memory:
    """
    Simulated shared resource that can hold up to `capacity` tokens total.
    """

    def __init__(self, env, capacity, threshold=1.0):
        self.env = env
        self.capacity = capacity
        self.vacancies = capacity
        self.threshold = threshold
        self.peak_usage = 0

    def request(self, amount):
        if amount > self.vacancies:
            return False
        else:
            self.vacancies -= amount
            if self.occupied_tokens > self.peak_usage:
                self.peak_usage = self.occupied_tokens
            return True

    def release(self, amount):
        self.vacancies += amount
        if self.vacancies > self.capacity:
            raise ValueError("Releasing more tokens than capacity.")
        return self.vacancies

    @property
    def occupied_tokens(self):
        return self.capacity - self.vacancies

    @property
    def available_tokens(self):
        return self.vacancies

    @property
    def safe_capacity(self):
        return self.capacity * self.threshold

    def __str__(self):
        return (
            f"Memory: {self.vacancies}/{self.capacity} tokens available, "
            f"Threshold {self.threshold} "
            f"(Peak: {self.peak_usage / self.capacity * 100:.1f}%)"
        )
