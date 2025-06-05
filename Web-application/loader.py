import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image as keras_image


model = load_model("weed_classifier.h5")  


IMG_SIZE = (224, 224)

def predict_image(img):
   
    img = img.resize(IMG_SIZE)
    
  
    img_array = keras_image.img_to_array(img)
    
    
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0  

    
    predictions = model.predict(img_array)
    
    
    predicted_class = np.argmax(predictions, axis=1)[0]

    class_labels = [
        'Aerva lanata', 'Amaranthus spinosus123', 'Calotropis plant123', 'Chinee apple',
        'Cleome viscosa', 'Cyprus rotundus', 'Datura', 'Lantana', 'Martynia Annua111', 
        'Negative', 'Parkinsonia', 'Parthenium', 'Phyllanthus nirur', 'Prickly acacia', 
        'Pycerus polystachyos', 'Rubber vine', 'Siam weed', 'Snake weed', 'Sorghum halepense', 
        'Taraxacum officinale', 'Trianthema portulacastrum', 'Tridax procumbens', 'Xanthium strumarium', 
        'abutilon hirtum123', 'acalypha indica123', 'cuscuta', 'digitaria sanguinalis', 'echinochloa colona', 
        'eichhornia crassipe', 'euphorbia prostrat', 'portulaca oleracea', 'serpyllifolia123'
    ]
    
   
    predicted_label = class_labels[predicted_class]

    return predicted_label
