import tensorflow as tf
import keras

# Load with current Keras 3.13.2
model = keras.models.load_model("companies_stock.h5", compile=False)

# Save in new format (Keras 3.x ka native format)
model.save("companies_stock.keras")

print("Done!")