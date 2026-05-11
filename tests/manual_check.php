<?php
/**
 * Manual check script to verify index.php without PHPUnit.
 */

$indexFile = dirname(__DIR__) . '/index.php';
$errors = [];

echo "Running manual checks for index.php...\n";

// 1. Syntax Check
$output = [];
$returnVar = 0;
exec("php -l " . escapeshellarg($indexFile), $output, $returnVar);
if ($returnVar !== 0) {
    $errors[] = "Syntax error in index.php: " . implode("\n", $output);
} else {
    echo "✓ Syntax check passed.\n";
}

// 2. Constant Check
$content = file_get_contents($indexFile);
$pattern = "/define\(\s*['\"]WP_USE_THEMES['\"]\s*,\s*true\s*\);/";
if (!preg_match($pattern, $content)) {
    $errors[] = "WP_USE_THEMES constant not defined correctly in index.php.";
} else {
    echo "✓ WP_USE_THEMES constant check passed.\n";
}

if (empty($errors)) {
    echo "ALL CHECKS PASSED!\n";
    exit(0);
} else {
    echo "CHECKS FAILED:\n";
    foreach ($errors as $error) {
        echo "- $error\n";
    }
    exit(1);
}
