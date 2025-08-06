import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/widgets/radioButton.dart';
import 'package:dishdive/pages/home.dart';
import 'package:dishdive/widgets/text_form.dart';
import 'package:dishdive/widgets/button_at_bottom.dart';
import 'package:dishdive/widgets/add_image.dart';
import 'package:provider/provider.dart';

class NewItemAdd extends StatefulWidget {
  const NewItemAdd({super.key});

  @override
  State<NewItemAdd> createState() => _NewItemAddState();
}

class _NewItemAddState extends State<NewItemAdd> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _itemNameController = TextEditingController();
  final TextEditingController _DescriptionController = TextEditingController();
  String _selectedValueForRadioButton = '';
  File? _selectedImage;

  Future<bool> addItem() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    const url = 'http://10.0.2.2:5428/PostAddItem';
    String fileName = 'image_${DateTime.now().millisecondsSinceEpoch}.jpg';
    try {
      var formData = FormData.fromMap({
        'itemname': _itemNameController.text ?? '',
        'description': _DescriptionController.text ?? '',
        'file': await MultipartFile.fromFile(
          _selectedImage!.path,
          filename: fileName,
        ),
        'offertype': _selectedValueForRadioButton ?? ''
      });

      final response = await Dio().post(
        url,
        data: formData,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json', // Adjust content type as needed
          },
        ),
      );

      if (response.statusCode == 200) {
        var map = response.data as Map;

        if (map['status'] == 'Successfully registered') {
          return true;
        }
        return true;
      } else {
        return false;
      }
    } catch (e) {
      return false;
    }
  }

  @override
  void dispose() {
    _itemNameController.dispose();
    _DescriptionController.dispose();
    if (_selectedImage != null) {
    _selectedImage!.delete(); // Attempt to delete the file
    _selectedImage = null; // Clear the reference
    }
    _selectedValueForRadioButton = '';
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isWeb = MediaQuery.of(context).platformBrightness == Brightness.dark;
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      appBar: AppBar(
        title: const Text(
          "Add New Item",
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Color.fromARGB(240, 255, 255, 255),
          ),
        ),
        centerTitle: true,
        automaticallyImplyLeading: false,
        backgroundColor: const Color(0xFF1B4D3F),
        elevation: 5,
        shadowColor: const Color.fromARGB(255, 171, 171, 171),
      ),
      body: SingleChildScrollView(
        child: Center(
          child: Container(
            width: isWeb ? 700 : 380,
            padding: const EdgeInsets.symmetric(vertical: 20.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                TextForm(
                  filled: true,
                  label: 'Item name',
                  controller: _itemNameController,
                ),
                // TextForm(
                //   label: 'Quantity',
                //   controller: _quantityController,
                // ),
                TextForm(
                  filled: true,
                  label: 'Description',
                  controller: _DescriptionController,
                  maxLine: 5,
                ),
                Radiobutton(title: 'Purpose', labels: const ['Looking to receive','Looking to donate'],
                onChanged: (value) {
                  if(value == 'Looking to receive'){
                    setState(() {
                      _selectedValueForRadioButton = 'Receive';
                    });
                  }else{
                    setState(() {
                      _selectedValueForRadioButton = 'Donate';
                    });
                  }
                },),
                Padding(
                  padding: const EdgeInsets.only(top: 20.0),
                  child: AddImage(
                    onImageSelected: (image) {
                      setState(() {
                        _selectedImage = image;
                      });
                                        },
                    textfill: 'Add image + ',
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(top: 20.0, bottom: 20),
                  child: ButtonAtBottom(
                    onPressed: () async {
                      bool success = await addItem();
                      if (success) {
                        print('true');
                        Navigator.push(
                            context,
                            MaterialPageRoute(
                                builder: (context) => const Home()));
                      }
                       else {
                        print('false not successful');
                      }
                    },
                    text: 'SUBMIT',
                    color: colorUse.activeButton,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
