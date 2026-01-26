# Language Support

The bot supports multiple languages with a global localization system.

## Auto-Detection (Optional)

Set `LANG` to `"AUTO_LANG"` to automatically detect the primary language for the region.

## Configuration

To configure the language, set the `LANG` field in `config.json`. We recommend setting this manually to your desired language code (e.g., `"es"` for Spanish). The language code is case-insensitive (e.g., `"ES"`, `"es"`, `"Es"` are all valid).

```json
{
  "LANG": "en" 
}
```

## Supported Languages

You can use any of the following codes in the `LANG` configuration:

| Language | Code |
| :--- | :--- |
| **English** | `en` |
| **Spanish** | `es` |
| **Portuguese** | `pt` |
| **French** | `fr` |
| **German** | `de` |
| **Italian** | `it` |
| **Dutch** | `nl` |
| **Turkish** | `tr` |
| **Polish** | `pl` |
| **Russian** | `ru` |
| **Indonesian**| `id` |
| **Greek** | `el` |
| **Romanian** | `ro` |
| **Hungarian** | `hu` |
| **Czech** | `cs` |
| **Ukrainian** | `uk` |
| **Arabic** | `ar` |
| **Chinese** | `zh` |

## Adding Languages / Customizing
To add more languages or customize texts, edit `src/config/languages.py`. 

### Emoji and Prefix Structure

This table shows the supported ICAO prefixes and their corresponding flag emojis. These are used when `COUNTRY_FLAG` and `COUNTRY_NAME` are set to `AUTO`.

| Prefix | Country | Emoji |
| :--- | :--- | :--- |
| **Europe (Northern)** | | |
| `EF` | Finland | 🇫🇮 |
| `EE` | Estonia | 🇪🇪 |
| `ES` | Sweden | 🇸🇪 |
| `EN` | Norway | 🇳🇴 |
| `EK` | Denmark | 🇩🇰 |
| `EV` | Latvia | 🇱🇻 |
| `EY` | Lithuania | 🇱🇹 |
| `BI` | Iceland | 🇮🇸 |
| **Europe (Western/Central)** | | |
| `EG` | UK | 🇬🇧 |
| `EI` | Ireland | 🇮🇪 |
| `EH` | Netherlands | 🇳🇱 |
| `EB` | Belgium | 🇧🇪 |
| `EL` | Luxembourg | 🇱🇺 |
| `LF` | France | 🇫🇷 |
| `ED`, `ET` | Germany | 🇩🇪 |
| `LO` | Austria | 🇦🇹 |
| `LS` | Switzerland | 🇨🇭 |
| `LI` | Italy | 🇮🇹 |
| `LE` | Spain | 🇪🇸 |
| `LP` | Portugal | 🇵🇹 |
| **Europe (Eastern/Southern)** | | |
| `EP` | Poland | 🇵🇱 |
| `LK` | Czechia | 🇨🇿 |
| `LZ` | Slovakia | 🇸🇰 |
| `LH` | Hungary | 🇭🇺 |
| `LJ` | Slovenia | 🇸🇮 |
| `LD` | Croatia | 🇭🇷 |
| `LQ` | Bosnia | 🇧🇦 |
| `LY` | Serbia | 🇷🇸 |
| `LW` | North Macedonia | 🇲🇰 |
| `LA` | Albania | 🇦🇱 |
| `LR` | Romania | 🇷🇴 |
| `LB` | Bulgaria | 🇧🇬 |
| `LG` | Greece | 🇬🇷 |
| `LC` | Cyprus | 🇨🇾 |
| `LT` | Turkey | 🇹🇷 |
| `LU` | Moldova | 🇲🇩 |
| `UM` | Belarus | 🇧🇾 |
| `UK` | Ukraine | 🇺🇦 |
| `U`  | Russia | 🇷🇺 |
| **North America** | | |
| `K` | USA | 🇺🇸 |
| `C` | Canada | 🇨🇦 |
| `MM` | Mexico | 🇲🇽 |
| **Central America / Caribbean** | | |
| `MY` | Bahamas | 🇧🇸 |
| `MU` | Cuba | 🇨🇺 |
| `MK` | Jamaica | 🇯🇲 |
| `MD` | Dominican Rep. | 🇩🇴 |
| `MT` | Haiti | 🇭🇹 |
| `TJ` | Puerto Rico | 🇵🇷 |
| `MW` | Cayman Islands | 🇰🇾 |
| `MG` | Guatemala | 🇬🇹 |
| `MH` | Honduras | 🇭🇳 |
| `MS` | El Salvador | 🇸🇻 |
| `MN` | Nicaragua | 🇳🇮 |
| `MR` | Costa Rica | 🇨🇷 |
| `MP` | Panama | 🇵🇦 |
| `MB` | Turks & Caicos | 🇹🇨 |
| `MZ` | Belize | 🇧🇿 |
| **South America** | | |
| `SK` | Colombia | 🇨🇴 |
| `SV` | Venezuela | 🇻🇪 |
| `SY` | Guyana | 🇬🇾 |
| `SM` | Suriname | 🇸🇷 |
| `SO` | French Guiana | 🇬🇫 |
| `SE` | Ecuador | 🇪🇨 |
| `SP` | Peru | 🇵🇪 |
| `SB`, `SD`, `SI`... | Brasil | 🇧🇷 |
| `SL` | Bolivia | 🇧🇴 |
| `SG` | Paraguay | 🇵🇾 |
| `SC` | Chile | 🇨🇱 |
| `SA` | Argentina | 🇦🇷 |
| `SU` | Uruguay | 🇺🇾 |
| **Asia** | | |
| `LL` | Israel | 🇮🇱 |
| `OJ` | Jordan | 🇯🇴 |
| `OS` | Syria | 🇸🇾 |
| `OL` | Lebanon | 🇱🇧 |
| `OR` | Iraq | 🇮🇶 |
| `OI` | Iran | 🇮🇷 |
| `OK` | Kuwait | 🇰🇼 |
| `OB` | Bahrain | 🇧🇭 |
| `OT` | Qatar | 🇶🇦 |
| `OE` | Saudi Arabia | 🇸🇦 |
| `OM` | UAE | 🇦🇪 |
| `OO` | Oman | 🇴🇲 |
| `OY` | Yemen | 🇾🇪 |
| `OA` | Afghanistan | 🇦🇫 |
| `OP` | Pakistan | 🇵🇰 |
| `VI`, `VA`, `VE`... | India | 🇮🇳 |
| `VC` | Sri Lanka | 🇱🇰 |
| `VR` | Maldives | 🇲🇻 |
| `VG` | Bangladesh | 🇧🇩 |
| `VN` | Nepal | 🇳🇵 |
| `VQ` | Bhutan | 🇧🇹 |
| `VY` | Myanmar | 🇲🇲 |
| `VT` | Thailand | 🇹🇭 |
| `VL` | Laos | 🇱🇦 |
| `VD` | Cambodia | 🇰🇭 |
| `VV` | Vietnam | 🇻🇳 |
| `WM` | Malaysia | 🇲🇾 |
| `WS` | Singapore | 🇸🇬 |
| `WB` | Brunei | 🇧🇳 |
| `WP` | Timor-Leste | 🇹🇱 |
| `WI`, `WA`, `WR`... | Indonesia | 🇮🇩 |
| `RP` | Philippines | 🇵🇭 |
| `RC` | Taiwan | 🇹🇼 |
| `RJ`, `RO` | Japan | 🇯🇵 |
| `RK` | South Korea | 🇰🇷 |
| `ZK` | North Korea | 🇰🇵 |
| `ZM` | Mongolia | 🇲🇳 |
| `Z` | China | 🇨🇳 |
| **Oceania** | | |
| `Y` | Australia | 🇦🇺 |
| `NZ` | New Zealand | 🇳🇿 |
| `AY` | PNG | 🇵🇬 |
| `AG` | Solomon Is. | 🇸🇧 |
| `AN` | Nauru | 🇳🇷 |
| `NF` | Fiji | 🇫🇫 |
| `NV` | Vanuatu | 🇻🇺 |
| `NW` | New Caledonia | 🇳🇨 |
| `NG` | Kiribati | 🇰🇮 |
| `NI` | Niue | 🇳🇺 |
| `NL` | Wallis & Futuna | 🇼🇫 |
| `NS` | Samoa | 🇼🇸 |
| `NT` | Fr. Polynesia | 🇵🇫 |
| **Africa** | | |
| `GM` | Morocco | 🇲🇦 |
| `DA` | Algeria | 🇩🇿 |
| `DT` | Tunisia | 🇹🇳 |
| `HL` | Libya | 🇱🇾 |
| `HE` | Egypt | 🇪🇬 |
| `GQ` | Mauritania | 🇲🇷 |
| `GO` | Senegal | 🇸🇳 |
| `GB` | Gambia | 🇬🇲 |
| `GU` | Guinea | 🇬🇳 |
| `GF` | Sierra Leone | 🇸🇱 |
| `GL` | Liberia | 🇱🇷 |
| `DI` | Cote d'Ivoire | 🇨🇮 |
| `DG` | Ghana | 🇬🇭 |
| `DX` | Togo | 🇹🇬 |
| `DB` | Benin | 🇧🇯 |
| `DN` | Nigeria | 🇳🇬 |
| `DF` | Burkina Faso | 🇧🇫 |
| `DR` | Niger | 🇳🇪 |
| `FT` | Chad | 🇹🇩 |
| `HK` | Kenya | 🇰🇪 |
| `HU` | Uganda | 🇺🇬 |
| `HT` | Tanzania | 🇹🇿 |
| `HR` | Rwanda | 🇷🇼 |
| `HB` | Burundi | 🇧🇮 |
| `HC` | Somalia | 🇸🇴 |
| `HA` | Ethiopia | 🇪🇹 |
| `HSS`, `HSO` | Sudan | 🇸🇩 |
| `FK` | Cameroon | 🇨🇲 |
| `FE` | CAR | 🇨🇫 |
| `FO` | Gabon | 🇬🇦 |
| `FC` | Congo | 🇨🇬 |
| `FZ` | DRC | 🇨🇩 |
| `FG` | Eq. Guinea | 🇬🇶 |
| `FN` | Angola | 🇦🇴 |
| `FB` | Botswana | 🇧🇼 |
| `FL` | Zambia | 🇿🇲 |
| `FV` | Zimbabwe | 🇿🇼 |
| `FW` | Malawi | 🇲🇼 |
| `FQ` | Mozambique | 🇲🇿 |
| `FA` | South Africa | 🇿🇦 |
| `FX` | Lesotho | 🇱🇸 |
| `FD` | Eswatini | 🇸🇿 |
| `FM` | Madagascar | 🇲🇬 |
| `FIM` | Mauritius | 🇲🇺 |
| `FS` | Seychelles | 🇸🇨 |
