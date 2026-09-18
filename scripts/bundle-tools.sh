#!/bin/bash
set -euo pipefail
cd "$SRCROOT"
resources="$TARGET_BUILD_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH"
mkdir -p "$resources/bin" "$resources/lib"
make all
cp build/device_helper build/airtraffic_host build/card_pdf "$resources/bin/"
# Override this when building on a Mac without an installed release.
deps="${AIRCARD_DEPENDENCIES:-/Applications/AirCard.app/Contents/Resources}"
for tool in ideviceinfo idevicesyslog; do
    if [[ ! -f "$deps/bin/$tool" ]]; then
        echo "error: Missing $deps/bin/$tool. Set AIRCARD_DEPENDENCIES to a release's Resources directory."
        exit 1
    fi
    cp "$deps/bin/$tool" "$resources/bin/"
done
cp -R "$deps/lib/." "$resources/lib/"
if [[ "${CODE_SIGNING_ALLOWED:-YES}" != NO ]]; then
    while IFS= read -r -d '' binary; do
        codesign --force --sign "${EXPANDED_CODE_SIGN_IDENTITY:--}" "$binary"
    done < <(find "$resources/bin" "$resources/lib" -type f -print0)
fi
