import 'package:flutter/material.dart';
import 'package:dishdive/widgets/MarketPlaceReceive.dart';

class DropDown extends StatefulWidget {
  const DropDown({super.key});

  @override
  _DropDownState createState() => _DropDownState();
}

class _DropDownState extends State<DropDown> {
  String _selectedItem = 'Receive';

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        DropdownButton<String>(
          value: _selectedItem,
          onChanged: (String? newValue) {
            setState(() {
              _selectedItem = newValue!;
            });
          },
          items: <String>['Donate', 'Receive'].map((String value) {
            return DropdownMenuItem<String>(
              value: value,
              child: Text(value),
            );
          }).toList(),
        ),
        _selectedItem == 'Receive'
            ? const MarketPlaceReceive()
            : const MarketPlaceReceive(),
      ],
    );
  }
}
