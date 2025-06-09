from reset_db import reset_db
import traceback

try:
    reset_db()
except Exception as e:
    print("Error occurred:")
    print(str(e))
    print("\nTraceback:")
    traceback.print_exc()
