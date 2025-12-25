# User Acceptance Testing (UAT) Guide

## Overview

User Acceptance Testing (UAT) validates that the system meets business requirements and is usable by end-users in real-world scenarios. Unlike functionality and performance testing, UAT focuses on:

- **User Experience**: Is the system intuitive and easy to use?
- **Business Requirements**: Does the system meet the actual needs of users?
- **Real-World Scenarios**: Can users complete their daily tasks?
- **Data Accuracy**: Is the water quality data reliable and accurate?
- **End-to-End Workflows**: Can users complete full workflows from start to finish?

---

## Difference from Other Testing Types

| Testing Type | Focus | Perspective |
|-------------|-------|-------------|
| **Functionality Testing** | Does it work? | Technical - verifies features function |
| **Performance Testing** | How fast/well? | Technical - measures speed and capacity |
| **Security Testing** | Is it secure? | Technical - verifies security measures |
| **UAT** | Does it meet user needs? | **User/Business** - validates real-world usage |

---

## Prerequisites

### Test Environment
- System deployed in UAT environment (as close to production as possible)
- Real or simulated sensor devices available
- Test users with different roles (if applicable)
- Access to web interface
- Network connectivity to MQTT broker

### Test Users
- **Primary Users**: Water quality monitoring personnel
- **Secondary Users**: Administrators, technicians
- **Stakeholders**: Business owners, decision makers

---

## UAT Test Scenarios

### UAT-001: New User Onboarding Journey

**Business Requirement**: New users should be able to register and start monitoring water quality within 15 minutes.

**User Story**: "As a new water quality technician, I want to register an account and set up my first sensor so I can start monitoring water quality."

**Test Steps**:
1. Navigate to registration page
2. Register new account with valid information
3. Receive confirmation (if applicable)
4. Log in with new credentials
5. Navigate to sensor registration
6. Register first sensor device:
   - Enter device ID
   - Select location
   - Select sensor type
   - Upload or generate public key
7. Verify sensor appears in dashboard
8. Verify sensor status is visible
9. Complete profile setup

**Success Criteria**:
- ✅ User can complete registration in < 5 minutes
- ✅ User can register first sensor in < 10 minutes
- ✅ All steps are intuitive and clear
- ✅ No technical knowledge required for basic setup
- ✅ User feels confident using the system

**Acceptance**: User can successfully onboard and start monitoring within 15 minutes

---

### UAT-002: Daily Water Quality Monitoring Workflow

**Business Requirement**: Users should be able to monitor water quality data in real-time and view historical trends.

**User Story**: "As a water quality technician, I need to check current water quality readings and compare them with historical data to identify trends."

**Test Steps**:
1. Log in to system
2. Navigate to dashboard
3. View current sensor readings:
   - pH levels
   - Temperature
   - Other sensor metrics
4. Verify data is current (within last few minutes)
5. Check sensor status (online/offline)
6. Navigate to "Live Readings" page
7. Verify real-time updates (if applicable)
8. Navigate to "History" page
9. Select a device
10. Select date range (last 7 days)
11. Review historical data and trends
12. Export data (if feature available)

**Success Criteria**:
- ✅ Current readings are visible within 30 seconds of login
- ✅ Data is clearly labeled and easy to understand
- ✅ Historical data loads in < 5 seconds
- ✅ Trends are visible (charts/graphs if available)
- ✅ User can identify normal vs. abnormal readings
- ✅ Data export works (if available)

**Acceptance**: User can efficiently monitor water quality and identify trends

---

### UAT-003: Sensor Device Management Workflow

**Business Requirement**: Users should be able to add, configure, and manage multiple sensor devices.

**User Story**: "As a water quality manager, I need to add new sensors, update device information, and remove old devices as monitoring needs change."

**Test Steps**:
1. Log in to system
2. Navigate to "Sensors" → "Manage Sensors"
3. View list of all registered sensors
4. Verify sensor information displayed:
   - Device ID
   - Location
   - Status (active/inactive)
   - Last update time
5. Add new sensor:
   - Click "Register Sensor"
   - Fill in device information
   - Complete registration
6. Verify new sensor appears in list
7. Edit existing sensor:
   - Select sensor to edit
   - Update location or other information
   - Save changes
8. Verify changes reflected in list
9. View sensor details
10. Delete a test sensor (if needed)

**Success Criteria**:
- ✅ All sensors are visible in organized list
- ✅ Adding new sensor is straightforward (< 3 minutes)
- ✅ Editing sensor information is easy
- ✅ Changes are immediately visible
- ✅ User can manage multiple sensors efficiently

**Acceptance**: User can manage sensor devices without technical assistance

---

### UAT-004: Data Accuracy and Reliability Validation

**Business Requirement**: Water quality data must be accurate and reliable for decision-making.

**User Story**: "As a water quality analyst, I need to trust that the sensor readings are accurate and reflect actual water conditions."

**Test Steps**:
1. Log in to system
2. Note current sensor readings (pH, temperature, etc.)
3. Compare with manual measurements (if possible) or known test values
4. Verify readings are within expected ranges
5. Monitor readings over time (30 minutes)
6. Verify readings change appropriately (if conditions change)
7. Check for any sudden unrealistic spikes or drops
8. Verify data consistency across multiple sensors (if applicable)
9. Review historical data for anomalies
10. Verify data timestamps are accurate

**Success Criteria**:
- ✅ Sensor readings are within expected accuracy range (±5% for pH, ±1°C for temperature)
- ✅ Data is consistent and reliable
- ✅ No unexplained data anomalies
- ✅ Timestamps are accurate
- ✅ User trusts the data for decision-making

**Acceptance**: Data accuracy meets business requirements for water quality monitoring

---

### UAT-005: Multi-Device Monitoring Scenario

**Business Requirement**: Users should be able to monitor multiple sensors simultaneously across different locations.

**User Story**: "As a water quality manager, I need to monitor sensors at multiple locations (e.g., different water sources) from a single dashboard."

**Test Steps**:
1. Log in to system
2. Register 3-5 sensors at different locations:
   - Location A: pH sensor
   - Location B: Temperature sensor
   - Location C: Combined sensor
3. Navigate to dashboard
4. Verify all sensors visible
5. Verify each sensor shows:
   - Correct location
   - Current readings
   - Status
6. Navigate to "Live Readings"
7. Verify all sensors display readings
8. Navigate to "History"
9. Select different devices
10. Verify data is correctly associated with each device
11. Verify no data mixing between devices

**Success Criteria**:
- ✅ All sensors visible on dashboard
- ✅ Data correctly associated with each device
- ✅ No confusion between different sensors
- ✅ User can easily identify which sensor is which
- ✅ Multi-location monitoring is efficient

**Acceptance**: System supports multi-device monitoring effectively

---

### UAT-006: Historical Data Analysis Workflow

**Business Requirement**: Users should be able to analyze historical data to identify patterns and trends.

**User Story**: "As a water quality analyst, I need to review historical data to identify trends, seasonal patterns, and potential issues."

**Test Steps**:
1. Ensure system has at least 1 week of historical data
2. Log in to system
3. Navigate to "History" page
4. Select a device
5. Select different date ranges:
   - Last 24 hours
   - Last 7 days
   - Last 30 days
   - Custom date range
6. Review data for each time period
7. Identify trends (if charts/graphs available)
8. Look for patterns:
   - Daily patterns
   - Weekly patterns
   - Anomalies
9. Export data for external analysis (if available)
10. Compare data across different time periods

**Success Criteria**:
- ✅ Historical data loads quickly (< 5 seconds)
- ✅ Date range selection works correctly
- ✅ Data visualization is clear (if charts available)
- ✅ Trends are identifiable
- ✅ User can analyze patterns effectively
- ✅ Export works (if available)

**Acceptance**: Historical data analysis supports decision-making

---

### UAT-007: System Usability and User Experience

**Business Requirement**: System should be intuitive and easy to use without extensive training.

**User Story**: "As a water quality technician with basic computer skills, I should be able to use the system effectively after minimal training."

**Test Steps**:
1. Have a new user (not familiar with system) attempt to:
   - Register account
   - Log in
   - View dashboard
   - Register a sensor
   - View historical data
2. Observe user behavior:
   - Can they find features easily?
   - Do they need help?
   - Are error messages clear?
   - Is navigation intuitive?
3. Test on different devices:
   - Desktop browser
   - Tablet (if responsive)
   - Mobile phone (if responsive)
4. Test with different browsers:
   - Chrome
   - Firefox
   - Edge
5. Verify accessibility:
   - Can users with basic computer skills use it?
   - Are labels and instructions clear?
   - Is help/documentation available?

**Success Criteria**:
- ✅ New user can complete basic tasks without help
- ✅ Navigation is intuitive
- ✅ Error messages are clear and helpful
- ✅ System works on common browsers
- ✅ Responsive design works (if applicable)
- ✅ User feels confident using the system

**Acceptance**: System is usable by target users with minimal training

---

### UAT-008: Profile and Account Management

**Business Requirement**: Users should be able to manage their account information and preferences.

**User Story**: "As a system user, I need to update my profile information and change my password when needed."

**Test Steps**:
1. Log in to system
2. Navigate to "Profile" page
3. View current profile information
4. Update profile:
   - Change full name
   - Update email address
   - Update other profile fields
5. Save changes
6. Verify changes saved
7. Log out and log back in
8. Verify updated information persists
9. Navigate to password change (if available)
10. Change password:
   - Enter current password
   - Enter new password
   - Confirm new password
11. Save password change
12. Log out
13. Log in with new password
14. Verify login successful

**Success Criteria**:
- ✅ Profile updates work correctly
- ✅ Changes persist after logout/login
- ✅ Password change works
- ✅ Old password no longer works
- ✅ Process is straightforward

**Acceptance**: Users can manage their accounts independently

---

### UAT-009: Real-World Sensor Integration

**Business Requirement**: System should work with actual sensor devices in real-world conditions.

**User Story**: "As a water quality technician, I need the system to receive and display data from actual physical sensors deployed in the field."

**Test Steps**:
1. Deploy actual sensor device (or use simulator that mimics real device)
2. Configure sensor to connect to MQTT broker
3. Register sensor in system
4. Verify sensor connects successfully
5. Send sensor data from device
6. Verify data appears in system:
   - Dashboard shows new reading
   - Live Readings page updates
   - Data appears in History
7. Monitor for extended period (1-2 hours):
   - Verify continuous data reception
   - Verify no data loss
   - Verify data accuracy
8. Test sensor disconnection:
   - Disconnect sensor
   - Verify status updates to "offline"
   - Reconnect sensor
   - Verify status updates to "online"
   - Verify data reception resumes

**Success Criteria**:
- ✅ Real sensor integrates successfully
- ✅ Data is received reliably
- ✅ No data loss during normal operation
- ✅ Status updates correctly
- ✅ System handles disconnections gracefully
- ✅ Data is accurate

**Acceptance**: System works reliably with actual sensor devices

---

### UAT-010: End-to-End Complete Workflow

**Business Requirement**: Users should be able to complete the full workflow from device setup to monitoring and analysis.

**User Story**: "As a water quality manager, I need to complete the entire workflow: register account, add sensors, monitor data, and analyze trends - all in one session."

**Test Steps**:
1. **Setup Phase** (15 minutes):
   - Register new account
   - Log in
   - Complete profile
   - Register 2-3 sensors
2. **Monitoring Phase** (30 minutes):
   - View dashboard
   - Check live readings
   - Verify sensor status
   - Monitor data updates
3. **Analysis Phase** (15 minutes):
   - Review historical data
   - Identify trends
   - Export data (if available)
4. **Management Phase** (10 minutes):
   - Update sensor information
   - Check system status
   - Review account settings

**Success Criteria**:
- ✅ Complete workflow can be done in one session
- ✅ No major issues or blockers
- ✅ User can accomplish all goals
- ✅ System remains responsive throughout
- ✅ User is satisfied with experience

**Acceptance**: Complete workflow is functional and efficient

---

## UAT Execution Guidelines

### Test Environment Setup
- Use environment as close to production as possible
- Use realistic test data
- Include actual or realistic sensor devices
- Test with real users (not just developers)

### Test Execution
1. **Prepare Test Scenarios**: Review all UAT scenarios
2. **Select Test Users**: Choose representative users
3. **Execute Tests**: Have users perform scenarios
4. **Observe and Document**: Note issues, feedback, and observations
5. **Collect Feedback**: Get user opinions and suggestions
6. **Document Results**: Record pass/fail for each scenario

### Success Criteria
- **Must Pass**: UAT-001, UAT-002, UAT-003, UAT-004, UAT-009, UAT-010
- **Should Pass**: UAT-005, UAT-006, UAT-007, UAT-008

### Acceptance Criteria
System is **ACCEPTED** if:
- ✅ All "Must Pass" scenarios pass
- ✅ At least 6 out of 10 scenarios pass
- ✅ No critical usability issues
- ✅ Users can complete primary workflows
- ✅ Data accuracy meets requirements

---

## UAT Test Report Template

### Test Execution Summary
- **Total Scenarios**: 10
- **Passed**: X
- **Failed**: Y
- **Blocked**: Z
- **Test Date**: [Date]
- **Tested By**: [User Names]

### Scenario Results

| Scenario ID | Scenario Name | Status | Notes |
|------------|---------------|--------|-------|
| UAT-001 | New User Onboarding | Pass/Fail | |
| UAT-002 | Daily Monitoring | Pass/Fail | |
| UAT-003 | Device Management | Pass/Fail | |
| UAT-004 | Data Accuracy | Pass/Fail | |
| UAT-005 | Multi-Device | Pass/Fail | |
| UAT-006 | Historical Analysis | Pass/Fail | |
| UAT-007 | Usability | Pass/Fail | |
| UAT-008 | Account Management | Pass/Fail | |
| UAT-009 | Real Sensor Integration | Pass/Fail | |
| UAT-010 | End-to-End Workflow | Pass/Fail | |

### User Feedback
- **Positive Feedback**: [What users liked]
- **Issues Found**: [Problems encountered]
- **Suggestions**: [User recommendations]
- **Overall Satisfaction**: [Rating/Comments]

### Acceptance Decision
- **Status**: ACCEPTED / NOT ACCEPTED / CONDITIONAL
- **Conditions**: [If conditional, what needs to be fixed]
- **Sign-off**: [Stakeholder approval]

---

## Related Test Documents

- **Functionality Testing**: `FUNCTIONALITY_AND_PERFORMANCE_TEST_CASES.md` - Technical feature verification
- **Performance Testing**: `FUNCTIONALITY_AND_PERFORMANCE_TEST_CASES.md` - Speed and capacity testing
- **Security Testing**: `STEP_BY_STEP_TESTING_GUIDE.md` - Security validation

---

## Notes

- UAT should be performed by actual end-users or stakeholders, not just developers
- Focus on real-world usage scenarios, not technical implementation
- Document user feedback and suggestions for improvements
- UAT results determine if system is ready for production deployment

---

This guide provides comprehensive UAT scenarios for validating the water monitoring system from a user and business perspective.

