
### New `CHANGELOG.md`

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [0.0.5] - 2024-12-02

### Added
- **Iframe Handling**: Enhanced the fuzzer to detect and interact with input fields within iframes. This includes switching between iframes and collecting input elements for fuzzing, expanding coverage to web applications that utilize iframes for form inputs.
- **Extended DOM Traversal**: Implemented deeper DOM traversal logic to detect and interact with dynamically loaded elements, hidden elements, and elements nested within complex page structures.
- **DOM Mutation Monitoring**: Injected JavaScript using `MutationObserver` to track changes in the DOM during fuzzing, providing better insight into dynamic content changes.
- **Improved User Console Output**: Console output during execution has been polished to provide a more readable, user-friendly summary of actions being taken by the fuzzer.


### Added
- `JavaScriptChangeDetector` now includes robust JavaScript error detection using both injected JavaScript and Chrome DevTools.
- State tracking feature with snapshot comparison before and after interactions.
- User-friendly logging for ChromeDriver startup.
- New payloads to the fuzzing payload list for broader test coverage.

### Changed
- Updated `create_driver` to remove deprecated `desired_capabilities` argument, ensuring compatibility with the latest Selenium version.
- Changed default `SELENIUM_HEADLESS` configuration to `False` (GUI mode enabled by default).
- Improved console logging readability for ChromeDriver startup messages and fuzzer progress.

### Fixed
- Fixed an issue where ChromeDriver would start in headless mode by default despite user settings.
- Resolved `WebDriver.__init__() got an unexpected keyword argument 'desired_capabilities'` error by using the appropriate method for setting capabilities.
- Improved JavaScriptChangeDetector to consistently capture console logs, addressing intermittent console log retrieval issues.
- Fixed incorrect state comparison handling for dropdown elements.

### Removed
- Removed deprecated or unused parameters from Selenium WebDriver setup.

## [0.0.2] - 2024-11-28
### Added
- Added `js_change_detector` argument to `Fuzzer` class to track JavaScript changes during fuzzing.
- Introduced DevTools integration to capture JavaScript errors and console logs.

### Changed
- Updated the directory structure to include separate modules for configuration and utility functions.
- Enhanced command-line argument handling to allow more flexibility in fuzzing operations.

### Fixed
- Addressed bugs in input fuzzing due to dynamic web elements causing `StaleElementReferenceException`.

## [Alpha 1] - 2024-11-25
### Initial Version
- Basic fuzzer implementation with input and dropdown interaction.
- Logging for all actions performed by the fuzzer.
