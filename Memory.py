class Memory:
    """
    Simulated shared resource that can hold up to `capacity` tokens total.
    """

    def __init__(self, env, capacity):
        self.env = env
        self.capacity = capacity
        self.vacancies = capacity

    def request(self, amount):
        if amount > self.vacancies:
            return False
        else:
            self.vacancies -= amount
            return True

    def release(self, amount):
        self.vacancies += amount
        if self.vacancies > self.capacity:
            raise ValueError("Releasing more tokens than capacity.")
        return self.vacancies

    def available_tokens(self):
        return self.vacancies

    def __str__(self):
        return f"Memory: {self.vacancies}/{self.capacity} tokens available"
