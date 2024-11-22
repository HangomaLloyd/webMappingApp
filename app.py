import pytesseract
from PIL import Image
import re
from flask import Flask, render_template, request
import folium

# Flask app setup
app = Flask(__name__)

# Helper function to clean extracted text
def clean_extracted_text(text):
    # Replace embedded dashes in latitude with a decimal point
    text = re.sub(r'(\d)-(\d)', r'\1.\2', text)

    # Remove extra spaces in longitude
    text = re.sub(r'(\d+)\.\s+(\d+)', r'\1.\2', text)

    return text

# Helper function to extract GPS coordinates
def extract_coordinates(extracted_text):
    print(f"Original Extracted Text: '{extracted_text}'")
    
    # Normalize text to handle multiple spaces
    extracted_text = " ".join(extracted_text.split())
    print(f"Normalized Extracted Text: '{extracted_text}'")
    
    # Clean the extracted text
    extracted_text = clean_extracted_text(extracted_text)
    print(f"Cleaned Extracted Text: '{extracted_text}'")
    
    # Updated regex pattern
    pattern = r"[$]?S?(-?\d+\.\d+)[^E]*E\s?(\d+\.\d+)"
    match = re.search(pattern, extracted_text)

    if match:
        lat = match.group(1)  # Latitude
        lon = match.group(2)  # Longitude

        print(f"Matched Latitude: {lat}, Longitude: {lon}")

        # Original GPS coordinates
        original_coordinates = [lat, lon]

        # Adjusted latitude: Add a negative sign if the text contains '$' or 'S'
        if "$" in extracted_text or "S" in extracted_text:
            lat = f"-{lat.lstrip('-')}"  # Ensure the latitude is negative and avoid double negatives

        # Adjusted GPS coordinates
        adjusted_coordinates = [lat, lon]

        # Return both original and adjusted coordinates
        return original_coordinates, adjusted_coordinates

    print("Regex did not match. Could not extract valid GPS coordinates.")
    return None, None

# Route to the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle image upload and processing
@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        # Get the uploaded image from the form
        file = request.files['image']
        img = Image.open(file.stream)
        
        # Extract text from the image using Tesseract
        extracted_text = pytesseract.image_to_string(img)
        print(f"Extracted Text from Image: {extracted_text}")
        
        # Extract GPS coordinates from the text
        original_coords, adjusted_coords = extract_coordinates(extracted_text)
        
        if original_coords and adjusted_coords:
            print(f"Extracted Original GPS Coordinates: {original_coords}")
            print(f"Extracted Adjusted GPS Coordinates: {adjusted_coords}")
            
            # Save both sets of coordinates to a text file
            coordinates_file_path = 'extracted_coordinates.txt'
            with open(coordinates_file_path, 'a') as file:
                file.write(f"Original Coordinates: {original_coords[0]}, {original_coords[1]}\n")
                file.write(f"Adjusted Coordinates: {adjusted_coords[0]}, {adjusted_coords[1]}\n\n")

            # Create a map centered on the adjusted coordinates
            latitude, longitude = float(adjusted_coords[0]), float(adjusted_coords[1])
            m = folium.Map(location=[latitude, longitude], zoom_start=12)

            # Add markers for both original and adjusted coordinates
            folium.Marker(
                [float(original_coords[0]), float(original_coords[1])],
                popup=f"Original Coordinates: {original_coords[0]}, {original_coords[1]}",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

            folium.Marker(
                [latitude, longitude],
                popup=f"Adjusted Coordinates: {adjusted_coords[0]}, {adjusted_coords[1]}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

            # Render the map HTML into a string
            map_html = m._repr_html_()

            # Return the map and extracted coordinates
            return render_template(
                'index.html', 
                map_html=map_html, 
                original_coords=original_coords, 
                adjusted_coords=adjusted_coords
            )
        else:
            # Handle cases where no valid GPS data is found
            return render_template('index.html', error="Could not extract valid GPS coordinates.")
    
    except Exception as e:
        # Print and display any errors during processing
        print(f"Error processing the image: {str(e)}")
        return render_template('index.html', error="Error processing the image. Please try again.")

if __name__ == '__main__':
    app.run(host=0.0.0.0 port=5000, debug=True)

