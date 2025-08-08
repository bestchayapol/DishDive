import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Components/integrate_model.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/widgets/card_widget.dart';
import 'package:provider/provider.dart';

class ChatLog extends StatefulWidget {
  const ChatLog({super.key});
  
  @override
  State<ChatLog> createState() => _ChatLogState();
}

class _ChatLogState extends State<ChatLog> {
  List<MessageLog> messages = [];
  int? userid;
  int? messageUserId;
  String? username;
  String? latestMessage;
  String? img;
  int? selfId;
  Timer? _timer;

    Future<List<MessageLog>> fetchChatLog() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    selfId = Provider.of<TokenProvider>(context, listen: false).userId;
    Dio dio = Dio();
    final response = await dio.get(
      'http://10.0.2.2:5428/GetMessagePageOfCurrentUser',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ),
    );

    if (response.statusCode == 200) {
      final parsedJson = response.data as List;
      List<MessageLog> items = parsedJson.map((json) => MessageLog.fromJson(json)).toList();
      print('12DOne');
      return items;
    } else {
      throw Exception('Failed to load items');
    }
  }

  void refreshList() {
    setState(() {
      // Trigger rebuild by updating state
      fetchChatLog(); // Re-fetch wishlists
    });
  }

   @override
  void initState() {
    super.initState();
    fetchChatLog(); // Initial fetch
    _startPolling(); // Start polling
  }

  @override
  void dispose() {
    _timer?.cancel(); // Cancel the timer when the widget is disposed
    super.dispose();
  }

    void _startPolling() {
    _timer = Timer.periodic(const Duration(seconds: 10), (timer) async {
      if (mounted) { 
        // Ensure the widget is mounted before updating state
        final newMessages = await fetchChatLog();
        if (newMessages.length != messages.length ||
            !_areListsEqual(newMessages, messages)) {
          setState(() {
            messages = newMessages;
          });
        }
      } else {
        _timer?.cancel(); // Cancel the timer if the widget is not mounted
      }
    });
  }

  // Helper function to compare message lists
  bool _areListsEqual(List<MessageLog> a, List<MessageLog> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }

  void _refreshChatLog() { // Add _refreshChatLog to trigger refresh
    fetchChatLog().then((newMessages) {
      setState(() {
        messages = newMessages;
      });
    });
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      appBar: AppBar(
        title: const Text(
          "Chat Log",
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
      body: Column(
        children: [
          Padding(
          padding: const EdgeInsets.all(12.0),  
          ),
          Expanded(child: 
          FutureBuilder<List<MessageLog>>(
            future: fetchChatLog(),
            builder:(context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting){
                return const Center(child: CircularProgressIndicator());
              }else if (snapshot.hasError){
                return Center(child: Text('Error: ${snapshot.error}'));
              } else {
                messages = snapshot.data!;
                if(messages.isEmpty){
                  return Center(
                    child: const Text('You don\'t have a message yet'),
                  );
                } else {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 50),
                    child: ListView.builder(
                          shrinkWrap: true,
                          itemCount: messages.length,
                          itemBuilder: (context, index) {
                            final messagesList = messages[index];
                            return messageCard(
                              userId: selfId?? 0,
                              messageUserId: messagesList.userid, 
                              username: messagesList.username, 
                              img: messagesList.user_pic, 
                              latestMessage: messagesList.latestMessage,
                              onRefresh: _refreshChatLog,
                              );
                          },
                    ),
                  );
                  
                }
              }
            },
          ))
        ],
      ),
    );
  }
}