import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/text_use.dart';
import 'package:dishdive/pages/home.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/widgets/button_at_bottom.dart';
import 'package:dishdive/widgets/title_bar.dart';
import 'package:provider/provider.dart';

class ItemDetails extends StatefulWidget {
  final int itemid;
  final String username;
  final VoidCallback? onUpdateBuy;
  // final int? userIdOfUser;
  const ItemDetails({
    super.key,
    required this.itemid,
    required this.username,
    this.onUpdateBuy,
  });

  @override
  State<ItemDetails> createState() => _ItemDetailsState();
}

class _ItemDetailsState extends State<ItemDetails> {
  int? userIdFromToken;

  @override
  void initState() {
    super.initState();
    fetchItem();
  }

  Future<Map<String, dynamic>> fetchItem() async {
    
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    Dio dio = Dio(); // Create a Dio instance
    final response = await dio.get(
      'http://10.0.2.2:5428/GetItemDetailsByItemId/${widget.itemid}',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json', // Adjust content type as needed
        },
      ),
    );

    if (response.statusCode == 200) {
      setState(() {
        userIdFromToken = userId;
      });
      return response.data;
    } else {
      throw Exception('Failed to load wishlists');
    }
    
  }
// /DeleteItemByItemId/:ItemID
  Future<void> deleteItem() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    Dio dio = Dio(); // Create a Dio instance
    final response = await dio.put(
      'http://10.0.2.2:5428/DeleteItemByItemId/${widget.itemid}',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json', // Adjust content type as needed
        },
      ),
    );

    if (response.statusCode == 200) {
      return null; 
    } else {
      throw Exception('Failed to deleteItem');
    }
  }

  // /PutAsk/:ItemID/:AskByUserID
  Future<void> putAskMarketplaceItem() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    Dio dio = Dio(); // Create a Dio instance
    final response = await dio.put(
      'http://10.0.2.2:5428/PutAsk/${widget.itemid}/${userId}',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json', // Adjust content type as needed
        },
      ),
    );

    if (response.statusCode == 200) {
      return null; 
    } else {
      throw Exception('Failed to deleteItem');
    }
  }

  // /PutTransactionReady/:ItemID
  Future<void> putTransactionReady() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    Dio dio = Dio(); // Create a Dio instance
    final response = await dio.put(
      'http://10.0.2.2:5428/PutTransactionReady/${widget.itemid}',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json', // Adjust content type as needed
        },
      ),
    );

    if (response.statusCode == 200) {
      return null; 
    } else {
      throw Exception('Failed to deleteItem');
    }
  }

    // /PutCompleteTransaction/:ItemID
  Future<void> PutCompleteTransaction() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    Dio dio = Dio(); // Create a Dio instance
    final response = await dio.put(
      'http://10.0.2.2:5428/PutCompleteTransaction/${widget.itemid}',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json', // Adjust content type as needed
        },
      ),
    );

    if (response.statusCode == 200) {
      return null; 
    } else {
      throw Exception('Failed to deleteItem');
    }
  }

   @override
  void dispose() {
    // Consider canceling any ongoing Dio requests or other resources here
    super.dispose();
  }




  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: fetchItem(),
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        }

        if (snapshot.hasData) {
          final wishdata = snapshot.data;
          final itemName = wishdata?['itemname'] ?? 'Unknown Item';
          final description = wishdata?['description'] ?? 'Unknown description';
          final pics = wishdata?['item_pic'] ?? 'Unknown pics';
          final userId = (wishdata?['user_id']) ?? 0;
          final askbyUserId = wishdata?['asked_by_user_id'] ?? 0;
          final alreadyGave = wishdata?['already_gave'] ?? null;
          final confirmFromOwner = wishdata?['con_from_item_owner'] ?? null;
          final confirmFromAsker = wishdata?['con_from_item_asker'] ?? null;
          final offerType = wishdata?['offer_type'] ?? 'Unknown offerType';
          final username = widget.username;
          // print(widget.itemid);
          return Scaffold(
            backgroundColor: colorUse.backgroundColor,
            appBar: CustomAppBarNavigation(
              backgroundColor: colorUse.backgroundColor,
              title: itemName,
              backDestination: const Home(),
            ),
            body: SingleChildScrollView(
              child: Container(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.start,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    const SizedBox(height: 30),
                    Image.network(
                      pics ??
                          'https://via.placeholder.com/350/FFFFFF/000000?text=Image+Not+Found', // Placeholder URL
                      width: MediaQuery.of(context).size.width * 0.8,
                      height: MediaQuery.of(context).size.height * 0.4,
                      errorBuilder: (context, error, stackTrace) {
                        // Optional: Handle image loading errors gracefully
                        return Image.network(
                          'https://via.placeholder.com/350/FFFFFF/000000?text=Image+Not+Found', // Fallback image
                          width: MediaQuery.of(context).size.width * 0.8,
                          height: MediaQuery.of(context).size.height * 0.4,
                        );
                      },
                    ),
                    const SizedBox(height: 25),
                    SizedBox(
                      width: double.infinity,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // RegularTextBold(
                          //   wishdata?.containsKey('price') == true
                          //       ? '\$${(wishdata?['price'] as num)}' ??
                          //           '\$0'
                          //       : '',
                          // ),
                          // const SizedBox(height: 10),
                          const Divider(color: Colors.grey),
                          const SizedBox(height: 20),
                          const Padding(
                            padding: EdgeInsets.only(left: 12),
                            child: RegularTextBold('Propose by'),
                          ),
                          Padding(
                            padding: const EdgeInsets.only(left: 12),
                            child: RegularText(
                                username), // Replace with actual data
                          ),
                          const SizedBox(height: 24),
                          const Padding(
                            padding: EdgeInsets.only(left: 12),
                            child: RegularTextBold('Description'),
                          ),
                          Padding(
                            padding: const EdgeInsets.only(left: 12),
                            child: RegularText(
                                description), // Replace with actual data
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                    
                    if (userId == userIdFromToken && alreadyGave == null)
                      ButtonAtBottom(
                        onPressed: () async {
                         await deleteItem();
                         Navigator.push(context, 
                          MaterialPageRoute(builder: (context) => Home()));
                          widget.onUpdateBuy;
                        },
                        text: 'Delete item',
                        color: colorUse.activeButton,
                      ),
                    if (alreadyGave == false && (confirmFromOwner == null || confirmFromAsker == null)
                        )
                      ButtonAtBottom(
                        onPressed: () async {
                         await putTransactionReady();
                         Navigator.push(context, 
                          MaterialPageRoute(builder: (context) => Home()));
                          widget.onUpdateBuy;
                        },
                        text: userId == userIdFromToken && confirmFromOwner == null ? 'Ready to transaction' 
                        : askbyUserId == userIdFromToken && confirmFromAsker == null ? 'Ready to transaction'
                        : 'Waiting for mutal ready',
                        color: userId == userIdFromToken && confirmFromOwner == null ? colorUse.activeButton 
                        : askbyUserId == userIdFromToken && confirmFromAsker == null ? colorUse.activeButton
                        : colorUse.activeButton,
                      ),
                      if (alreadyGave == false && ((confirmFromAsker!=null && confirmFromOwner != null)
                          && (confirmFromOwner == false || confirmFromAsker == false))
                          && (confirmFromOwner != null || confirmFromOwner != true) &&
                              (confirmFromAsker != null || confirmFromAsker != true))
                      ButtonAtBottom(
                        onPressed: () async {
                         await PutCompleteTransaction();
                         Navigator.push(context, 
                          MaterialPageRoute(builder: (context) => Home()));
                          widget.onUpdateBuy;
                        },
                        text: userId == userIdFromToken && confirmFromOwner == false ? 'finishing transaction' 
                        : askbyUserId == userIdFromToken && confirmFromAsker == false ? 'finishing transaction'
                        : 'Waiting for mutal confirmation',
                        color: userId == userIdFromToken && confirmFromOwner == false ? colorUse.activeButton 
                        : askbyUserId == userIdFromToken && confirmFromAsker == false ? colorUse.activeButton
                        : colorUse.activeButton,
                      ),
                    //marketplace
                    if ((userId != userIdFromToken && offerType == 'Receive') 
                        && alreadyGave == null
                        )
                      ButtonAtBottom(
                        onPressed: () async {
                          await putAskMarketplaceItem();
                          Navigator.push(context, 
                          MaterialPageRoute(builder: (context) => Home()));
                          widget.onUpdateBuy;
                        },
                        text: 'Donate',
                        color: colorUse.activeButton,
                      ),

                    if (userId != userIdFromToken && offerType == 'Donate' 
                        && alreadyGave == null)
                      ButtonAtBottom(
                        onPressed: () async {
                          await putAskMarketplaceItem();
                          Navigator.push(context, 
                          MaterialPageRoute(builder: (context) => Home()));
                          widget.onUpdateBuy;
                        },
                        text: 'Ask for Receive',
                        color: colorUse.activeButton,
                      ),
                  ],
                ),
              ),
            ),
          );
        }

        return const Center(child: CircularProgressIndicator());
      },
    );
  }
}
