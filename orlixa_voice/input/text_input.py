class TextInput:
    def get_input(self):
        try:
            return input("\nType your command: ").strip()
        except KeyboardInterrupt:
            return None
        except Exception as e:
            return None
