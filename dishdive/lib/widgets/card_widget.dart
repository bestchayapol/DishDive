// import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Pages/Chats/ChatRoom.dart';
import 'package:dishdive/Pages/Item/Item_details.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/text_use.dart';
// import 'package:provider/provider.dart';
// import 'package:sweet_favors/pages/Wish/wish_details.dart';
// import 'package:sweet_favors/provider/token_provider.dart';


class CardWidget extends StatelessWidget {
  final String product;
  final String? askBy;
  final int itemlistId;
  final String? username;
  final int? userid;
  final bool? alreadyGave;
  final int? askedByUserId;
  final String description;
  final VoidCallback? onUpdate;
  final VoidCallback? onUpdateBuy;

  const CardWidget({
    super.key,
    required this.product,
    this.askBy,
    required this.itemlistId,
    required this.description,
    this.username,
    this.userid,
    this.alreadyGave,
    this.askedByUserId,
    this.onUpdate,
    this.onUpdateBuy,
  });

  @override
  Widget build(BuildContext context) {
    // Future<Map<String, dynamic>> _RecieverGotIt() async {
    //   final token = Provider.of<TokenProvider>(context, listen: false).token;
    //   final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    //   Dio dio = Dio(); // Create a Dio instance
    //   final response = await dio.put(
    //     'http://10.0.2.2:1432/UpdateReceiverGotIt/$wishlistId/$grantedByUserId',
    //     options: Options(
    //       headers: {
    //         'Authorization': 'Bearer $token',
    //         'Content-Type': 'application/json', // Adjust content type as needed
    //       },
    //     ),
    //   );

    //   if (response.statusCode == 200) {
    //     return response.data;
    //   } else {
    //     throw Exception('Failed to put _RecieverGotIt');
    //   }
    // }

    // Future<Map<String, dynamic>> _RecieverDidntGetit() async {
    //   // final token = Provider.of<TokenProvider>(context, listen: false).token;
    //   // final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    //   Dio dio = Dio(); // Create a Dio instance
    //   final response = await dio.put(
    //     'http://10.0.2.2:1432/UpdateReceiverDidntGetIt/$wishlistId/$grantedByUserId',
    //     options: Options(
    //       headers: {
    //         'Authorization': 'Bearer $token',
    //         'Content-Type': 'application/json', // Adjust content type as needed
    //       },
    //     ),
    //   );

    //   if (response.statusCode == 200) {
    //     return response.data;
    //   } else {
    //     throw Exception('Failed to put _RecieverDidntGetit');
    //   }
    // }

    return Center(
      child: Container(
        margin: const EdgeInsets.only(bottom: 25),
        child: InkWell(
          onTap: () {
            if (askedByUserId == null && alreadyGave == null) {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ItemDetails(
                    itemid: itemlistId,
                    username: username ?? 'null',
                    onUpdateBuy: onUpdateBuy,
                  ),
                ),
              );
            } else if (askedByUserId != null && alreadyGave == false) {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ItemDetails(
                    itemid: itemlistId,
                    username: username ?? 'null',
                    onUpdateBuy: onUpdateBuy,
                  ),
                ),
              );
              // showDialog(
              //     context: context,
              //     builder: (BuildContext dialogContext) {
              //       return PopUp(
              //         title: 'Did you recieved the wish?',
              //         buttons: [
              //           ButtonForPopUp(
              //               onPressed: () async {
              //                 Navigator.of(dialogContext).pop();
              //                 // await _RecieverGotIt();
              //                 onUpdate!();
              //               },
              //               text: 'Yes'),
              //           ButtonForPopUp(
              //               onPressed: () async {
              //                 Navigator.of(dialogContext).pop();
              //                 // await _RecieverDidntGetit();
              //                 onUpdate!();
              //               },
              //               text: 'No'),
              //         ],
              //       );
              //     });
            } else if (askedByUserId != null && alreadyGave == true) {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ItemDetails(
                    itemid: itemlistId,
                    username: username ?? 'null',
                    onUpdateBuy: onUpdateBuy,
                  ),
                ),
              );
            }
          },
          child: Card(
            // margin: EdgeInsets.only(bottom: 25),
            color: askedByUserId == null && alreadyGave == null
                ? colorUse.activeButton // Green (granted and bought)
                : (askedByUserId != null && alreadyGave == false)
                    ? const Color(0xFFFCDDA2)
                    : (askedByUserId != null && alreadyGave == true)
                    ? colorUse.activeButton : colorUse.rejectButton,
            elevation: 7,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                const SizedBox(height: 10.0),
                ListTile(
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16.0, vertical: 8.0),
                  title: Padding(
                    padding: const EdgeInsets.only(bottom: 10.0),
                    child: Text(
                      product,
                      style: TextStyles.cardTitleStyle().merge(TextStyle(
                          color: askedByUserId == null && alreadyGave == null
                                ? Colors.white // Green (granted and bought)
                                : (askedByUserId != null && alreadyGave == false)
                                    ? Colors.black
                                    : (askedByUserId != null && alreadyGave == true)
                                    ? Colors.white : Colors.white,
                              )),
                    ),
                  ),
                ),
                const SizedBox(height: 10.0),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class ProfileCard extends StatelessWidget {
  final String product;
  final Widget? destination;
  final IconData icon;
  const ProfileCard(
      {super.key, required this.product, this.destination, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        margin: const EdgeInsets.only(bottom: 15),
        child: InkWell(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => destination!,
                // builder: (context) => WishDetails(product: product, grantBy: grantBy),
              ),
            );
          },
          child: Card(
            // margin: EdgeInsets.only(bottom: 25),
            color: colorUse.secondaryColor,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                const SizedBox(height: 10.0),
                ListTile(
                  leading: Icon(icon),
                  title: RegularText(product),
                ),
                const SizedBox(height: 10.0),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class messageCard extends StatelessWidget {
  final int userId;
  final int messageUserId;
  final String username;
  final String? latestMessage;
  final String img;
  final VoidCallback? onRefresh;

  const messageCard(
      {super.key,
      required this.userId,
      required this.messageUserId,
      required this.username,
      this.latestMessage,
      required this.img,
      this.onRefresh,
      });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => ChatRoom(
              userId: userId, messageUserId: messageUserId, messageUsername: username,action: onRefresh,
            )),
          );
        },
        child: Card(
          color: colorUse.backgroundColor,
          child: Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: <Widget>[
                // Avatar (Using CachedNetworkImage for error handling)
                CircleAvatar(
                  radius: 28,
                  backgroundImage: NetworkImage(
                    img,
                  ),
                ),
                const SizedBox(width: 15),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      // Username
                      Text(
                        username,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 4),
                      // Latest Message
                      Text(
                        latestMessage ?? '', 
                        overflow: TextOverflow.ellipsis,
                        maxLines: 1,
                        style: const TextStyle(fontSize: 14),
                      ),
                    ],
                  ),
                ),
              ], // Removed the SizedBox and Text for the timestamp
            ),
          ),
        ),
      ),
    );
  }
}