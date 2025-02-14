# Home Assistant Whoop Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

This is a custom component for Home Assistant that integrates with the Whoop API to provide sensor data from your Whoop device.

## Features

- Recovery Score
- Sleep Score and Duration
- Strain Score
- Resting Heart Rate
- Additional metrics like HRV and Blood Oxygen Level

## Installation

### HACS Installation (Preferred)

1. Open HACS in your Home Assistant instance
2. Click on Integrations
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/whoop` folder to your `custom_components` directory in your Home Assistant config
3. Restart Home Assistant

## Configuration

1. Get your Whoop API Access Token:
   - Visit [Whoop Developer Portal](https://developer.whoop.com)
   - Create a new application
   - Generate an access token

2. In Home Assistant:
   - Go to Configuration > Integrations
   - Click the "+ Add Integration" button
   - Search for "Whoop"
   - Enter your access token when prompted

## Available Sensors

| Sensor             | Description               | Unit  |
|--------------------|---------------------------|-------|
| Recovery Score     | Daily recovery percentage |   %   |
| Sleep Score        | Sleep quality score       |   %   |
| Sleep Duration     | Total sleep time          | hours |
| Strain Score       | Daily strain level        | score |
| Resting Heart Rate | Resting heart rate        |  bpm  |
|--------------------|---------------------------|-------|
## Troubleshooting

### Common Issues

1. **Cannot Connect**: 
   - Verify your internet connection
   - Check if the Whoop API is accessible

2. **Invalid Authentication**:
   - Verify your access token is correct
   - Check if your token has expired

3. **No Data**:
   - Ensure your Whoop device is synced
   - Wait for the next update interval (5 minutes)

## Contributing

Feel free to contribute to this project by:
1. Reporting bugs
2. Suggesting new features
3. Creating pull requests

## License

This project is licensed under the MIT License - see the LICENSE file for details.