import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class AddImage extends StatefulWidget {
  final Function(File) onImageSelected;
  final String textfill;

  const AddImage(
      {super.key, required this.onImageSelected, required this.textfill});

  @override
  _AddImageState createState() => _AddImageState();
}

class _AddImageState extends State<AddImage> {
  File? _imageFile;

  Future<File?> getImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);
    if (image == null) {
      return null;
    } else {
      return File(image.path);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        margin: const EdgeInsets.only(bottom: 25),
        child: InkWell(
          onTap: () async {
            File? image = await getImage();
            if (image != null) {
              setState(() {
                _imageFile = image;
              });
              widget.onImageSelected(image);
            }
          },
          child: Card(
            color: const Color.fromARGB(255, 222, 247, 220),
            child: Padding(
              padding: const EdgeInsets.only(
                  top: 40, left: 40, right: 40, bottom: 30),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(8.0),
                  child: _imageFile != null
                      ? Image.file(_imageFile!, // Show selected image
                          width: 170,
                          height: 170,
                          fit: BoxFit.cover)
                      : const Icon(
                          Icons.image,
                          size: 30,
                        ), // Placeholder
                ),
                const SizedBox(height: 20),
                Text(
                  widget.textfill,
                  style: const TextStyle(
                    fontSize: 14.0,
                    color: Color.fromARGB(255, 27, 28, 50),
                  ),
                ),
              ]),
            ),
          ),
        ),
      ),
    );
  }
}
