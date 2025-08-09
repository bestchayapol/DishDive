import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

// CHANGES:
// - Removed unnecessary margin and Center widget
// - Used SizedBox for consistent sizing
// - Used BoxDecoration for rounded corners and shadow
// - Cleaned up image/icon logic
// - Improved padding and alignment

class AddImage extends StatefulWidget {
  final Function(File) onImageSelected;
  final String textfill;

  const AddImage({
    super.key,
    required this.onImageSelected,
    required this.textfill,
  });

  @override
  State<AddImage> createState() => _AddImageState();
}

class _AddImageState extends State<AddImage> {
  File? _imageFile;

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      setState(() {
        _imageFile = File(image.path);
      });
      widget.onImageSelected(_imageFile!);
    }
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: _pickImage,
      child: Container(
        width: 200,
        height: 210,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.07),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8.0),
              child: _imageFile != null
                  ? Image.file(
                      _imageFile!,
                      width: 90,
                      height: 90,
                      fit: BoxFit.cover,
                    )
                  : Container(
                      width: 90,
                      height: 90,
                      color: Colors.grey[200],
                      child: const Icon(
                        Icons.image,
                        size: 36,
                        color: Colors.grey,
                      ),
                    ),
            ),
            const SizedBox(height: 18),
            Text(
              widget.textfill,
              style: const TextStyle(
                fontSize: 15.0,
                color: Color.fromARGB(255, 27, 28, 50),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
