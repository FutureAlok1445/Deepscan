class HeartbeatValidator:
    def validate(self, signal, heart_rate):
        if 40 <= heart_rate <= 150: return True, "Valid physiological range"
        return False, "Abnormal or missing vital signs detected"