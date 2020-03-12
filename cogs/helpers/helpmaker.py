import discord


class Help:

    def make(self, author, name, commands):
        description = ""
        description = description + f'Hello {author}.\n'
        description = description + f'Invoke send command by entering `!{name} <subcommand> <arguments>`\n'
        description = description + f'Subcommand list :\n'
        for command in commands:
            command = commands[command]
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

        embed = discord.Embed(title=f'Help for !{name}', description=description)
        return embed
