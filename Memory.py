import simpy

class Memory:
    """
    Simulated shared resource that can hold up to `capacity` tokens total.
    """

    def __init__(self, env, capacity):
        self.env = env
        self.capacity = capacity
        self.container = simpy.Container(env, init=capacity, capacity=capacity)

    def request(self, amount):
        return self.container.get(amount)

    def release(self, amount):
        return self.container.put(amount)

    def available_tokens(self):
        return self.container.level

    def __str__(self):
        return f"Memory: {self.available_tokens()}/{self.capacity} tokens available"
