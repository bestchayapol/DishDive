// import 'package:dio/dio.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Components/profile_bar.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/widgets/ListView.dart';
import 'package:dishdive/widgets/MapView.dart';
import 'package:dishdive/components/my_textfield.dart';
import 'package:dishdive/components/integrate_model.dart' as components;
import 'package:provider/provider.dart';

class FirstHomePage extends StatefulWidget {
  const FirstHomePage({super.key});

  @override
  State<FirstHomePage> createState() => _FirstHomePageState();
}

class _FirstHomePageState extends State<FirstHomePage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String? username;
  String? email;
  String? img;
  String? firstname;
  String? lastname;
  String? fullname;
  int? userid;
  List<components.Itemlist> items = [];

  @override
  void initState() {
    super.initState();
    fetchUserData();
    // fetchItems();
    _tabController = TabController(length: 2, vsync: this);
  }

  Future<void> fetchUserData() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    Dio dio = Dio();
    final response = await dio.get(
      'http://10.0.2.2:5428/GetProfileOfCurrentUserByUserId/$userId',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json', // Adjust content type as needed
        },
      ),
    );

    if (response.statusCode == 200) {
      final parsedJson = response.data; // Directly get the parsed data
      setState(() {
        // Update the username and email variables with the parsed user data
        username = parsedJson['username'];
        email = parsedJson['email'];
        img = parsedJson['user_pic'];
        firstname = parsedJson['firstname'];
        lastname = parsedJson['lastname'];
        fullname = '$firstname $lastname';
        userid = userId;
      });
    } else {
      throw Exception('Failed to load user data');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      body: Column(
        children: [
          // Top black section with profile icon and search bar
          Container(
            color: colorUse.appBarColor,
            padding: const EdgeInsets.only(
              top: 40,
              left: 16,
              right: 16,
              bottom: 18,
            ),
            child: Column(
              children: [
                // Row for profile icon (right-aligned)
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    // Placeholder for profile image (grey sphere)
                    Container(
                      width: 48,
                      height: 48,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.grey, // Placeholder color
                      ),
                      // Uncomment below to use actual profile image:
                      // child: img != null
                      //     ? ClipOval(
                      //         child: Image.network(
                      //           img!,
                      //           width: 48,
                      //           height: 48,
                      //           fit: BoxFit.cover,
                      //         ),
                      //       )
                      //     : null,
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                // Search bar
                MyTextField(
                  hintText: "Search dish",
                  obscureText: false,
                  controller: TextEditingController(),
                  border: true,
                  // Optionally, you can add a prefix icon if your MyTextField supports it:
                  iconData: Icons.search,
                ),
              ],
            ),
          ),
          // Toggle button (TabBar)
          Container(
            color: colorUse.backgroundColor,
            child: TabBar(
              controller: _tabController,
              tabs: [
                Tab(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      vertical: 8,
                      horizontal: 24,
                    ),
                    child: const Text('List View'),
                  ),
                ),
                Tab(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      vertical: 8,
                      horizontal: 24,
                    ),
                    child: const Text('Map View'),
                  ),
                ),
              ],
              indicator: BoxDecoration(
                color: colorUse.activeButton,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: colorUse.activeButton, width: 2),
              ),
              indicatorSize: TabBarIndicatorSize.tab,
              labelColor: Colors.white,
              unselectedLabelColor: colorUse.activeButton,
              labelStyle: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
              unselectedLabelStyle: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
              dividerColor: Colors.transparent,
            ),
          ),
          // TabBarView for content
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: const [ListViewWidget(), MapViewWidget()],
            ),
          ),
        ],
      ),
    );
  }
}
