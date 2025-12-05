<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graph Example</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>Dynamic Graph with PHP and Chart.js</h1>
    <canvas id="myChart" width="400" height="200"></canvas>
</body>
</html>
<?php
// Sample data
$dataPoints = [12, 19, 3, 5, 2, 3];
$labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];

// Pass data to JavaScript
echo "<script>
    const dataPoints = " . json_encode($dataPoints) . ";
    const labels = " . json_encode($labels) . ";
</script>";
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graph Example</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>Dynamic Graph with PHP and Chart.js</h1>
    <canvas id="myChart" width="400" height="200"></canvas>

    <?php
    // Sample data
    $dataPoints = [12, 19, 3, 5, 2, 3];
    $labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];

    // Pass data to JavaScript
    echo "<script>
        const dataPoints = " . json_encode($dataPoints) . ";
        const labels = " . json_encode($labels) . ";
    </script>";
    ?>

    <script>
        // JavaScript to render the chart
        const ctx = document.getElementById('myChart').getContext('2d');
        const myChart = new Chart(ctx, {
            type: 'bar', // Change to 'line', 'pie', etc., for different graph types
            data: {
                labels: labels,
                datasets: [{
                    label: 'Data Points',
                    data: dataPoints,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>
