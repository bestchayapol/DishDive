import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/api_config.dart';
import 'package:dishdive/Pages/Profile/profile.dart';
import 'package:dishdive/widgets/ListView.dart';
import 'package:dishdive/widgets/MapView.dart';
import 'package:dishdive/widgets/modal_filter.dart';
import 'package:dishdive/components/my_textfield.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:provider/provider.dart';

class FirstHomePage extends StatefulWidget {
  const FirstHomePage({super.key});

  @override
  State<FirstHomePage> createState() => _FirstHomePageState();
}

class _FirstHomePageState extends State<FirstHomePage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();
  String? username;
  String? profileImageUrl;
  int? userid;
  List<Map<String, dynamic>> restaurants = [];
  bool isLoadingRestaurants = false;
  bool isSearching = false;

  @override
  void initState() {
    super.initState();
    fetchUserData();
    fetchRestaurants();
    _tabController = TabController(length: 2, vsync: this);
    
    // Add listener to search controller
    _searchController.addListener(() {
      _onSearchChanged(_searchController.text);
    });
  }

  Future<void> fetchUserData() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    
    if (token == null || userId == null) {
      return;
    }

    try {
      Dio dio = Dio();
      final response = await dio.get(
        ApiConfig.getProfileOfCurrentUserByUserIdEndpoint(userId),
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        final parsedJson = response.data;
        setState(() {
          profileImageUrl = parsedJson['image_link'];
          username = parsedJson['username'];
          userid = userId;
        });
      }
    } catch (e) {
      print('Error fetching user data: $e');
      // Handle error silently for now
    }
  }

  Future<void> fetchRestaurants() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    
    if (token == null) {
      return;
    }

    setState(() {
      isLoadingRestaurants = true;
    });

    try {
      Dio dio = Dio();
      final response = await dio.get(
        ApiConfig.getRestaurantListEndpoint,
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        final List<dynamic> restaurantData = response.data;
        setState(() {
          restaurants = restaurantData.map((restaurant) => {
            'id': restaurant['res_id'],
            'name': restaurant['res_name'] ?? 'Unknown Restaurant',
            'cuisine': restaurant['cuisine'] ?? 'Mixed',
            'distance': '${(restaurant['locations'] as List).isNotEmpty ? '0.5' : '0.0'} km away', // Placeholder since distance calculation needs user location
            'imageUrl': restaurant['image_link'] ?? '',
            'locations': restaurant['locations'] ?? [],
          }).toList();
          isLoadingRestaurants = false;
        });
      }
    } catch (e) {
      print('Error fetching restaurants: $e');
      setState(() {
        isLoadingRestaurants = false;
      });
    }
  }

  Future<void> searchRestaurantsByDish(String query) async {
    if (query.trim().isEmpty) {
      fetchRestaurants(); // Reset to full list
      return;
    }

    final token = Provider.of<TokenProvider>(context, listen: false).token;
    
    if (token == null) {
      return;
    }

    setState(() {
      isSearching = true;
    });

    try {
      Dio dio = Dio();
      final response = await dio.post(
        ApiConfig.searchRestaurantsByDishEndpoint,
        data: {'dish_name': query},
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        final List<dynamic> searchResults = response.data;
        setState(() {
          restaurants = searchResults.map((restaurant) => {
            'id': restaurant['res_id'],
            'name': restaurant['res_name'] ?? 'Unknown Restaurant',
            'cuisine': restaurant['cuisine'] ?? 'Mixed',
            'distance': '${restaurant['distance']?.toStringAsFixed(1) ?? '0.0'} km away',
            'imageUrl': restaurant['image_link'] ?? '',
            'location': restaurant['location'] ?? {},
          }).toList();
          isSearching = false;
        });
      }
    } catch (e) {
      print('Error searching restaurants: $e');
      setState(() {
        isSearching = false;
      });
    }
  }

  void _onSearchChanged(String value) {
    // Add debouncing to avoid too many API calls
    Future.delayed(const Duration(milliseconds: 500), () {
      if (_searchController.text == value) {
        searchRestaurantsByDish(value);
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  void _showFilterModal() {
    showDialog(context: context, builder: (context) => const FilterModal());
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
                    GestureDetector(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => Profile()),
                        );
                      },
                      child: Container(
                        width: 48,
                        height: 48,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.grey, // Placeholder color
                        ),
                        child: profileImageUrl != null && profileImageUrl!.isNotEmpty
                            ? ClipOval(
                                child: Image.network(
                                  profileImageUrl!,
                                  width: 48,
                                  height: 48,
                                  fit: BoxFit.cover,
                                  errorBuilder: (context, error, stackTrace) {
                                    return const Icon(
                                      Icons.person,
                                      color: Colors.white,
                                      size: 24,
                                    );
                                  },
                                  loadingBuilder: (context, child, loadingProgress) {
                                    if (loadingProgress == null) return child;
                                    return const Center(
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                      ),
                                    );
                                  },
                                ),
                              )
                            : const Icon(
                                Icons.person,
                                color: Colors.white,
                                size: 24,
                              ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                // Search bar
                Row(
                  children: [
                    Expanded(
                      child: MyTextField(
                        hintText: "Search dish",
                        obscureText: false,
                        controller: _searchController,
                        border: true,
                        iconData: Icons.search,
                      ),
                    ),
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: _showFilterModal,
                      child: Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                          color: colorUse.activeButton,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(
                          Icons.filter_alt,
                          color: Colors.white,
                          size: 28,
                        ),
                      ),
                    ),
                  ],
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
                      vertical: 4,
                      horizontal: 24,
                    ),
                    child: const Text('List View'),
                  ),
                ),
                Tab(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      vertical: 4,
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
                fontFamily: 'InriaSans',
                fontWeight: FontWeight.normal,
                fontSize: 28,
              ),
              unselectedLabelStyle: const TextStyle(
                fontFamily: 'InriaSans',
                fontWeight: FontWeight.normal,
                fontSize: 28,
              ),
              dividerColor: Colors.transparent,
            ),
          ),
          // TabBarView for content
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                ListViewWidget(
                  restaurants: restaurants,
                  isLoading: isLoadingRestaurants || isSearching,
                ),
                const MapViewWidget(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
