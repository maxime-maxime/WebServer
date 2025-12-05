<?php

class Database
{
    private static ?\PDO $pdo = null;

    private const DB_HOST = 'Localhost';
    private const DB_NAME = 'maman';
    private const DB_USER = 'root';
    private const DB_PASS = '';
    private const DB_CHARSET = 'utf8mb4';

    public static function getConnection(): \PDO
    {
        if (self::$pdo === null) {
            $dsn = 'mysql:host=' . self::DB_HOST . ';dbname=' . self::DB_NAME . ';charset=' . self::DB_CHARSET;
            $options = [
                \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
                \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
                \PDO::ATTR_EMULATE_PREPARES => false,
            ];
            self::$pdo = new \PDO($dsn, self::DB_USER, self::DB_PASS, $options);
        }
        return self::$pdo;
    }
}