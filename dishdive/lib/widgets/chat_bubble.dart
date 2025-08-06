import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Components/integrate_model.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/text_use.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:provider/provider.dart';

class ChatBubble extends StatefulWidget {
  final int messageUserId;
  final int userId;
  final String messageUsername;
  final VoidCallback? onMessageSent;


  const ChatBubble({
    super.key,
    required this.userId,
    required this.messageUserId,
    required this.messageUsername,
    this.onMessageSent,
    });

  @override
  State<ChatBubble> createState() => _ChatBubbleState();
}

class _ChatBubbleState extends State<ChatBubble> {
  List<ChatMessages> userMessage = [];
  Timer? _timer;
  final ScrollController _scrollController = ScrollController();



  @override
  void initState() {
    super.initState();
    fetchChatMessages();
    _startPolling(); // Start polling
  }

  @override
  void dispose() {
    _scrollController.dispose(); 
    _timer?.cancel(); // Cancel the timer when the widget is disposed
    super.dispose();
  }

    void _startPolling() {
    _timer = Timer.periodic(const Duration(seconds: 10), (timer) async {
      if (mounted) { 
        // Ensure the widget is mounted before updating state
        final newMessages = await fetchChatMessages();
        if (newMessages.length != userMessage.length ||
            !_areListsEqual(newMessages, userMessage)) {
          setState(() {
            userMessage = newMessages;
          });
        }
      } else {
        _timer?.cancel(); // Cancel the timer if the widget is not mounted
      }
    });
  }

  // Helper function to compare message lists
  bool _areListsEqual(List<ChatMessages> a, List<ChatMessages> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }


      Future<List<ChatMessages>> fetchChatMessages() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    Dio dio = Dio();
    final response = await dio.get(
      'http://10.0.2.2:5428/GetConversationOfCurrentUserByOtherId/${widget.messageUserId}',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ),
    );

    if (response.statusCode == 200) {
      final parsedJson = response.data as List;
      List<ChatMessages> messages = parsedJson.map((json) => ChatMessages.fromJson(json)).toList();
      return messages;
    } else {
      throw Exception('Failed to load items');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      child: 
        FutureBuilder<List<ChatMessages>>(
            future: fetchChatMessages(),
            builder:(context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting){
                return const Center(child: CircularProgressIndicator());
              }else if (snapshot.hasError){
                return Center(child: Text('Error: ${snapshot.error}'));
              } else {
                userMessage = snapshot.data!;
                if(userMessage.isEmpty){
                  return Center(
                    child: const Text('You don\'t have a message yet'),
                  );
                } else {
                  return Container(
                    child: ListView.builder(
                          controller: _scrollController,
                          reverse: true,
                          shrinkWrap: true,
                          itemCount: userMessage.length,
                          itemBuilder: (context, index) {
                          final message = userMessage[index];
                          bool isMe = message.userid == widget.userId; // Check if the message is mine
                          bool showAvatar = index == 0 || userMessage[index - 1].userid != message.userid; 

                          return Align(
                            alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                            child: Container( 
                              // isMe ? (isLastConsecutive ? const Radius.circular(12) : Radius.zero) : const Radius.circular(12),
                              padding: isMe ? (!showAvatar ? const EdgeInsets.only(right: 50) : EdgeInsets.all(4.0) ) 
                                            : (!showAvatar ? const EdgeInsets.only(left: 50) : EdgeInsets.all(4.0) ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                // Reorder based on 'isMe'
                                children: [
                                 if (!isMe && showAvatar)
                                  CircleAvatar(backgroundImage: NetworkImage(message.user_pic)),
                                  const SizedBox(width: 8),
                                  Flexible(
                                    child: Container(
                                      constraints: BoxConstraints(maxWidth: 180),
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: isMe ? colorUse.activeButton : Colors.grey[200],
                                        borderRadius: BorderRadius.only(
                                          topLeft: const Radius.circular(12),
                                          topRight: const Radius.circular(12),
                                          bottomRight: isMe ? (!showAvatar ? const Radius.circular(12) : Radius.zero) : const Radius.circular(12),
                                          bottomLeft: isMe ? const Radius.circular(12) : (!showAvatar ? const Radius.circular(12) : Radius.zero),
                                        ),
                                      ),
                                      child: RegularText(message.msgText),
                                    ),
                                  ),
                                  // RegularText(message.message),
                                  if (isMe && showAvatar) const SizedBox(width: 8), // Add space before avatar for my message
                                  if (isMe && showAvatar)
                                    CircleAvatar(backgroundImage: NetworkImage(message.user_pic)),
                                ],
                              ),
                            ),
                          );
                        },
                      )
                  );
                }
              }
            },
          )
    );
  }
}