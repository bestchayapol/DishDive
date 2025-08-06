import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/widgets/chat_bubble.dart';
import 'package:dishdive/widgets/text_form.dart';
import 'package:dishdive/widgets/title_bar.dart';
import 'package:provider/provider.dart';

class ChatRoom extends StatefulWidget {
  final int messageUserId;
  final int userId;
  final String messageUsername;
  final VoidCallback? action;

  const ChatRoom({super.key, required this.messageUserId, required this.userId, required this.messageUsername, this.action});

  @override
  State<ChatRoom> createState() => _ChatRoomState();
}

class _ChatRoomState extends State<ChatRoom> {
  final TextEditingController _messageController = TextEditingController();
  // bool _isButtonPressed = false;
		// SenderUserID:   message.SenderUserID,
		// ReceiverUserID: message.ReceiverUserID,
		// MsgText:        message.MsgText,

  Future<void> sendMessage() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    var formData = FormData.fromMap({
        'SenderUserID': widget.userId,
        'ReceiverUserID': widget.messageUserId,
        'MsgText': _messageController.text ,
    
    });
    if(_messageController.text != ''){
      final response = await Dio().post(
        'http://10.0.2.2:5428/PostMessage/${widget.messageUserId}',
        data: formData,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
            },
          ),
        );
      if (response.statusCode == 200) {
      _messageController.clear();
      if (widget.action != null) {
        widget.action!(); // Call the callback to refresh ChatLog
      }
      setState(() {});
     }
    }
  }



  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }
  
  

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      appBar: CustomAppBarPop(
        backgroundColor: colorUse.primaryColor,
        title: 'Chat',
        centerTitle: true,
        onPop: () {
          Navigator.pop(context, true);
          setState(() {
            widget.action!();
          });
        },
      ),
      body: Column(
        children: [
          Flexible( // UserInfo part
            flex: 1,
            fit: FlexFit.loose,
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    widget.messageUsername,
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w500),
                  ),
                  // const Icon(Icons.more_horiz)
                ],
              ),
            ),
          ),
          Expanded(
            flex: 6,
            // fit: FlexFit.tight,
            child: ChatBubble(
              userId: widget.userId,
              messageUserId: widget.messageUserId,
              messageUsername: widget.messageUsername,
            ),
          ),
          // Fixed bottom input area
          Padding(
            padding: EdgeInsets.all(2),
            child: Container(
              // flex: 2,
              // fit: FlexFit.tight,
              child: Container( // Wrap input area in a Container
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Column(
                  children: [
                    // ElevatedButton(
                    //   child: _isButtonPressed ? Text('Complete transaction',style: TextStyle(color: const Color(0xFF000000))) 
                    //                           : Text('Transaction ready',style: TextStyle(color: Colors.white)),
                    //   style: ElevatedButton.styleFrom(
                    //     backgroundColor: _isButtonPressed ? colorUse.accent : colorUse.primaryColor,
                    //     shape: RoundedRectangleBorder(
                    //       borderRadius: BorderRadius.circular(12)
                    //     )
                    //   ),
                    //   onPressed: () {
                    //     setState(() {
                    //       _isButtonPressed = !_isButtonPressed; // Toggle the pressed state
                    //     });
                    //   },
                    // ),
                    TextForm(
                      decorationAsSendIcon: true,
                      label: 'Start Typing...',
                      filled: true,
                      maxLine: 1,
                      controller: _messageController,
                      onSend: sendMessage,
                    ),
                  ],
                ),
              ),
            ),
          ), 
        ],
      ),
    );
  }
}