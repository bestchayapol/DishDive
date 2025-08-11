import 'dart:io';

import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
// Commented out for static data example
// import 'package:dio/dio.dart';
// import 'package:provider/provider.dart';;

class SetBlack extends StatefulWidget {
  const SetBlack({super.key});

  @override
  State<SetBlack> createState() => _SetBlackState();
}

class _SetBlackState extends State<SetBlack> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      appBar: AppBar(
        backgroundColor: colorUse.appBarColor,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          "Set Blacklist",
          style: TextStyle(
            fontFamily: 'InriaSans',
            fontWeight: FontWeight.bold,
            fontSize: 32,
            color: Colors.white,
          ),
        ),
        centerTitle: true,
      ),
    );
  }
}
