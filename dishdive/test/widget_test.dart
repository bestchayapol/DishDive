// This is a basic Flutter widget test for DishDive app.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:dishdive/main.dart';
import 'package:dishdive/provider/token_provider.dart';

void main() {
  testWidgets('DishDive app initializes correctly', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (context) => TokenProvider()),
          ChangeNotifierProvider(create: (context) => WelcomeProvider()),
        ],
        child: const MainApp(),
      ),
    );

    // Wait for the app to settle
    await tester.pumpAndSettle();

    // Verify that the app loads without crashing
    // Since the app shows different screens based on authentication state,
    // we just verify that a MaterialApp is rendered
    expect(find.byType(MaterialApp), findsOneWidget);
  });

  testWidgets('TokenProvider initializes correctly', (WidgetTester tester) async {
    // Test that TokenProvider can be created without errors
    final tokenProvider = TokenProvider();
    expect(tokenProvider.isAuthenticated, false);
    expect(tokenProvider.token, null);
    expect(tokenProvider.userId, null);
  });

  testWidgets('WelcomeProvider initializes correctly', (WidgetTester tester) async {
    // Test that WelcomeProvider can be created without errors
    final welcomeProvider = WelcomeProvider();
    expect(welcomeProvider.isWelcomeShown, false);
  });
}
