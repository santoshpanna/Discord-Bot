import discord


class Help:

    def make(self, author, name, directcommands, groupedcommands, extra):
        description = ""
        description = description + f'Hello {author}.\n'
        if directcommands:
            description = description + f'Invoke command by entering `!<command> arguments`\n'
            description = description + f'Command list :\n'
            for command in directcommands:
                if 'arguments' in command:
                    description = description + f'**{directcommands[command]["name"]}** ***{directcommands[command]["arguments"]}*** - {directcommands[command]["description"]}\n'
                else:
                    description = description + f'**{directcommands[command]["name"]}** - {directcommands[command]["description"]}\n'
            description = description + '\n'
        if groupedcommands:
            description = description + f'Invoke command by entering `!{name} <subcommand> <arguments>`\n'
            description = description + f'Subcommand list :\n'
            for command in groupedcommands:
                command = groupedcommands[command]
                if 'subcommand' in command:
                    subcommand = command['subcommand']
                    for subsubcommand in subcommand:
                        if 'name' in command and 'description' in command:
                            if 'arguments' in command:
                                description = description + f'**{command["name"]}** ***{command["arguments"]}*** - {command["description"]}\n'
                            else:
                                description = description + f'**{command["name"]}** - {command["description"]}\n'
                        if 'arguments' in subcommand[subsubcommand]:
                            description = description + f'**{subcommand[subsubcommand]["name"]}** ***{subcommand[subsubcommand]["arguments"]}*** - {subcommand[subsubcommand]["description"]}\n'
                        else:
                            description = description + f'**{subcommand[subsubcommand]["name"]}** - {subcommand[subsubcommand]["description"]}\n'
                elif 'arguments' in command and 'subcommand' not in command:
                    description = description + f'**{command["name"]}** ***{command["arguments"]}*** - {command["description"]}\n'
                else:
                    description = description + f'**{command["name"]}** - {command["description"]}\n'

        if extra:
            description = description + f'\n{extra}\n'

        embed = discord.Embed(title=f'Help for !{name}', description=description)
        return embed
