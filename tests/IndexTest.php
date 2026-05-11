<?php

namespace Tests;

use PHPUnit\Framework\TestCase;

class IndexTest extends TestCase
{
    /**
     * Test that index.php has no syntax errors.
     */
    public function testIndexSyntax(): void
    {
        $indexFile = dirname(__DIR__) . '/index.php';
        $output = [];
        $returnVar = 0;
        exec("php -l " . escapeshellarg($indexFile), $output, $returnVar);
        $this->assertEquals(0, $returnVar, 'index.php has syntax errors: ' . implode("\n", $output));
    }

    /**
     * Test that index.php defines WP_USE_THEMES as true.
     */
    public function testWpUseThemesConstantIsDefined(): void
    {
        $indexFile = dirname(__DIR__) . '/index.php';
        $content = file_get_contents($indexFile);

        // Use regex to ensure the constant is defined correctly
        // Matches: define( 'WP_USE_THEMES', true );
        $pattern = "/define\(\s*['\"]WP_USE_THEMES['\"]\s*,\s*true\s*\);/";
        $this->assertMatchesRegularExpression($pattern, $content, 'index.php does not define WP_USE_THEMES as true');
    }
}
