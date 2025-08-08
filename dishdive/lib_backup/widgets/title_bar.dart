import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/text_use.dart';
// Import your Home page

class CustomAppBarNavigation extends StatelessWidget
    implements PreferredSizeWidget {
  final String title;
  final bool centerTitle; // Added parameter for title alignment
  final Widget? backDestination;
  final Color? backgroundColor;

  const CustomAppBarNavigation({
    super.key,
    required this.title,
    this.centerTitle = false,
    this.backDestination,
    this.backgroundColor
  });

  @override
  Widget build(BuildContext context) {
    return AppBar(
      backgroundColor: backgroundColor,
      centerTitle: centerTitle ? true : false,
      title: Heading(title),
      leading: IconButton(
        onPressed: () => Navigator.pop(context),
        icon: const Icon(Icons.arrow_back, color: Colors.black),
      ),
    );
  }

  @override
  Size get preferredSize =>
      const Size.fromHeight(kToolbarHeight); // Standard AppBar height
}

class CustomAppBarPop extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final bool centerTitle; // Added parameter for title alignment
  final Color? backgroundColor;
  final VoidCallback? onPop;

  const CustomAppBarPop(
      {super.key, required this.title, this.centerTitle = false, this.backgroundColor, this.onPop});


  @override
  Widget build(BuildContext context) {

    return AppBar(
      backgroundColor: backgroundColor,
      centerTitle: centerTitle ? true : false,
      title: Text(
          title,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Color.fromARGB(240, 255, 255, 255),
          ),
        ),
      elevation: 5,
      shadowColor: const Color.fromARGB(255, 171, 171, 171),
      automaticallyImplyLeading: false,
      leading: IconButton(
        onPressed: () {
          if(onPop != null){
            onPop!();
          }else{
            Navigator.pop(context);
          }
        },
        icon: const Icon(Icons.arrow_back, color: Color.fromARGB(255, 255, 255, 255)),
      ),
    );
  }

  @override
  Size get preferredSize =>
      const Size.fromHeight(kToolbarHeight); // Standard AppBar height
}

class CustomAppBarPopNoTitle extends StatelessWidget
    implements PreferredSizeWidget {
  final bool centerTitle; // Added parameter for title alignment

  const CustomAppBarPopNoTitle({super.key, this.centerTitle = false});

  @override
  Widget build(BuildContext context) {
    return AppBar(
      backgroundColor: colorUse.primaryColor,
      centerTitle: centerTitle ? true : false,
      leading: IconButton(
        onPressed: () => Navigator.pop(context),
        icon: const Icon(Icons.arrow_back, color: Color.fromARGB(255, 255, 255, 255)),
      ),
    );
  }

  @override
  Size get preferredSize =>
      const Size.fromHeight(kToolbarHeight); // Standard AppBar height
}
