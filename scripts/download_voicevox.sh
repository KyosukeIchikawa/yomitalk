#!/bin/bash
# Script to download and setup VOICEVOX Core
# This script handles the download and setup of VOICEVOX Core with proper error handling

set -e  # Exit immediately if a command exits with a non-zero status

# Default values
VOICEVOX_VERSION="0.16.0"
VOICEVOX_DIR="voicevox_core"
SKIP_IF_EXISTS=false
ACCEPT_AGREEMENT=false

# Help message
show_help() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  --version VERSION       VOICEVOX Core version to download (default: $VOICEVOX_VERSION)"
  echo "  --dir DIR               Directory to install VOICEVOX Core (default: $VOICEVOX_DIR)"
  echo "  --skip-if-exists        Skip download only if VOICEVOX files already exist"
  echo "  --accept-agreement      Auto-accept VOICEVOX license agreement"
  echo "  -h, --help              Show this help message"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      VOICEVOX_VERSION="$2"
      shift 2
      ;;
    --dir)
      VOICEVOX_DIR="$2"
      shift 2
      ;;
    --skip-if-exists)
      SKIP_IF_EXISTS=true
      shift
      ;;
    --skip-download)  # 以前のフラグもサポート（互換性のため）
      SKIP_IF_EXISTS=true
      shift
      ;;
    --accept-agreement)
      ACCEPT_AGREEMENT=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Error: Unknown option: $1" >&2
      show_help
      exit 1
      ;;
  esac
done

# Function to check if VOICEVOX Core is already installed
check_voicevox_installed() {
  local voicevox_dir="$1"

  # Check if directory exists
  if [ ! -d "$voicevox_dir" ]; then
    return 1
  fi

  # Check for library files
  if find "$voicevox_dir" -name "*.so" -o -name "*.dll" -o -name "*.dylib" | grep -q .; then
    return 0
  else
    return 1
  fi
}

# Function to download VOICEVOX Core
download_voicevox_core() {
  local version="$1"
  local voicevox_dir="$2"
  local accept_agreement="$3"

  # Create directory if it doesn't exist
  mkdir -p "$voicevox_dir"

  # Download the downloader script
  local downloader_url="https://github.com/VOICEVOX/voicevox_core/releases/download/${version}/download-linux-x64"
  local downloader_path="${voicevox_dir}/download"

  echo "Downloading VOICEVOX Core downloader version ${version}..."
  if ! curl -L -o "$downloader_path" "$downloader_url"; then
    echo "Error: Failed to download VOICEVOX downloader"
    return 1
  fi

  # Make the downloader executable
  chmod +x "$downloader_path"

  # Run the downloader
  echo "Downloading VOICEVOX Core components..."
  cd "$voicevox_dir" || { echo "Error: Failed to change directory to $voicevox_dir"; return 1; }

  if [ "$accept_agreement" = true ]; then
    echo "Auto-accepting license agreement"
    echo "y" | ./download --devices cpu
    if [ $? -ne 0 ]; then
      echo "Error: Failed to download VOICEVOX Core components"
      return 1
    fi
  else
    ./download --devices cpu
    if [ $? -ne 0 ]; then
      echo "Error: Failed to download VOICEVOX Core components"
      return 1
    fi
  fi

  return 0
}

# Main script logic
main() {
  if [ "$SKIP_IF_EXISTS" = true ] && check_voicevox_installed "$VOICEVOX_DIR"; then
    echo "VOICEVOX Core files already exist, skipping download (--skip-if-exists flag set)."
    return 0
  fi

  if check_voicevox_installed "$VOICEVOX_DIR"; then
    echo "VOICEVOX Core files already exist, skipping download."
    return 0
  fi

  echo "VOICEVOX Core not found or missing necessary library files. Starting download..."
  if download_voicevox_core "$VOICEVOX_VERSION" "$VOICEVOX_DIR" "$ACCEPT_AGREEMENT"; then
    echo "VOICEVOX Core files downloaded successfully!"
    return 0
  else
    echo "Failed to download VOICEVOX Core."
    return 1
  fi
}

# Run the main function
main
exit $?
