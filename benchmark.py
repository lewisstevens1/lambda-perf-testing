"""
Benchmark tool for measuring Lambda function performance in different memory
sizes.
"""

from __future__ import print_function
import argparse
import math
import base64
import boto3

MEMORY_TO_PRICE = {
    128: 0.0000002083,
    512: 0.0000008333,
    1024: 0.0000016667,
    1536: 0.0000025000,
    2048: 0.0000033333,
    3008: 0.0000048958
}

PRICE_INTERVAL = 100
INVOCATIONS_COUNT = 5
CSV_HEADER = 'Size,Duration (in ms),Price Per 1M Invocations (in $)\n'


def invoke_lambda_and_get_duration(lambda_client, payload, function_name):
    """
    Invokes Lambda and return the duration.
    :param lambda_client: Lambda client.
    :param payload: payload to send.
    :param function_name: function name.
    :return: duration.
    """
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=payload,
    )

    # Extract duration from Lambda log
    lambda_log = base64.b64decode(response['LogResult']).decode('utf-8')
    report_data = \
        [line for line in lambda_log.split('\n')
         if line.startswith('REPORT')
        ][0]
    duration = \
        [col for col in report_data.split('\t')
         if col.startswith('Duration')
         ][0]
    duration = float(duration.split()[1])
    return duration


def run_benchmark(args):
    """
    Run benchmark.
    :param args: arguments.
    :return: None.
    """
    
    results = {}
    payload_files = [{
        "name": "payload-sm",
        "path": "fibonacci-function/payload-sm.json"
    },{   
        "name": "payload-md",
        "path": "fibonacci-function/payload-md.json"
    },{
        "name": "payload-lg",
        "path": "fibonacci-function/payload-lg.json"
    }]
    
    for payload_object in payload_files:

        results[payload_object.get("name")] = {}
        
        if args.aws_profile:
            aws_session = boto3.Session(profile_name=args.aws_profile)
        else:
            aws_session = boto3.Session()

        lambda_client = aws_session.client('lambda', region_name=args.region)
        sorted_memory_sizes = sorted(MEMORY_TO_PRICE)

        # Load payload
        with open(payload_object.get("path"), 'rt') as input_data:
            payload = input_data.read()

        # Read Original memory size
        original_memory_size = lambda_client.get_function_configuration(
            FunctionName=args.function_name,
        )['MemorySize']
        print('Original memory size ({0}): {1}MB'.format(payload_object.get("name"),original_memory_size))
        print('-' * 50)

        # Benchmark
        for memory_size in sorted_memory_sizes:
            print('Setting memory size: {0}MB'.format(memory_size))
            lambda_client.update_function_configuration(
                FunctionName=args.function_name,
                MemorySize=memory_size,
            )

            lambda_client.invoke(
                FunctionName=args.function_name,
                Payload=payload,
            )

            # Run several times
            duration_sum = 0
            for _ in range(INVOCATIONS_COUNT):
                duration_sum += invoke_lambda_and_get_duration(
                    lambda_client,
                    payload,
                    args.function_name
                )

            duration = duration_sum / INVOCATIONS_COUNT
            results[payload_object.get("name")][memory_size] = duration
            print('-' * 50)

        lambda_client.update_function_configuration(
            FunctionName=args.function_name,
            MemorySize=original_memory_size,
        )
    
    with open(args.output_file, 'wt') as output_results:
        output_results.write(CSV_HEADER)
        
        for payload_object in payload_files:
            for memory_size in sorted_memory_sizes:
                name = payload_object.get("name")
                price = math.ceil(results[name][memory_size] / PRICE_INTERVAL) \
                        * MEMORY_TO_PRICE[memory_size] * 1000000

                output_results.write('{0},{1},{2}\n'.format(
                    '{0} [{1}MB]'.format(name, memory_size),
                    '%.2f' % (results[name][memory_size],),
                    '%.2f' % (price,)
                ))
    
    print("Output written to results.csv")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Benchmark Lambda function with several memory sizes to' +
        'understand the impact on performance.'
    )

    parser.add_argument(
        '-f',
        '--function',
        dest='function_name',
        default=False,
        required=True,
        help='Tested function name.'
    )
    parser.add_argument(
        '-r',
        '--region',
        dest='region',
        default=False,
        required=True,
        help='Tested function region.'
    )
    parser.add_argument(
        '--profile',
        dest='aws_profile',
        default=False,
        required=False,
        help='A specific AWS Named Profile configured within your AWS Credentials file.'
    )
    parser.add_argument(
        '--output',
        dest='output_file',
        default='results.csv',
        help='Output results filename.'
    )

    arguments = parser.parse_args()
    run_benchmark(arguments)
