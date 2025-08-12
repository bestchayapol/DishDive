import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/widgets/list_favorites.dart';
// Commented out for static data example
// import 'package:dio/dio.dart';
// import 'package:provider/provider.dart';;

class SetPref extends StatefulWidget {
  const SetPref({super.key});

  @override
  State<SetPref> createState() => _SetPrefState();
}

class _SetPrefState extends State<SetPref> {
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
          "Set Preferences",
          style: TextStyle(
            fontFamily: 'InriaSans',
            fontWeight: FontWeight.bold,
            fontSize: 32,
            color: Colors.white,
          ),
        ),
        centerTitle: true,
      ),
      body: Column(children: [Expanded(child: ListFavoritesWidget())]),
    );
  }
}
