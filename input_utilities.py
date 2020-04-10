def retrieve_numerical_input(query_string, n):
    user_input = input(query_string)
    while not (user_input.isnumeric() and 0 <= int(user_input) <= n):
        print("Oops, looks like that wasn't a valid number.")
        user_input = input(query_string)
    return int(user_input)
