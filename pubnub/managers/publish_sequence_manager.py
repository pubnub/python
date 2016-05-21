class PublishSequenceManager:
    def __init__(self, provided_max_sequence):
        self.max_sequence = provided_max_sequence
        self.next_sequence = 0

    # TODO: should be thread-safe
    def get_next_sequence(self):
        if self.max_sequence == self.next_sequence:
            self.next_sequence = 1
        else:
            self.next_sequence += 1

        return self.next_sequence
