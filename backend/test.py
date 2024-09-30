import exifread

# Open the image file for reading (in binary mode)
with open("static/uploads/images/toasty.jpg", 'rb') as image_file:
    # Pass the image file to exifread for reading the EXIF data
    exif_data = exifread.process_file(image_file)

# Loop through all EXIF tags
for tag in exif_data.keys():
    # Print the tag and its corresponding value
    print(f"{tag}: {exif_data[tag]}")

