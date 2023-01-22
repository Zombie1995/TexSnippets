# TexSnippets

[Ссылка на статью habr](https://habr.com/ru/post/711830/)

## Основные проблемы, решенные при помощи этих сниппетов

### Быстрое вхождение в математический режим

Для быстрого написания формул была назначена замена "ьл" (mk), на $$. Чтобы быстро выйти с таких скобок достаточно нажать на tab.

### Расстановка индексов

Чтобы поставить верхний, нижний индекс нужно использовать "^" и "_" соответственно. Более того, если оно будеть состоять более чем из одной буквы, то придется использовать фигурные скобки "{}", что уменьшает удобство.

На стандартной клавиатуре это делать неудобно, поэтому я назначил "," на нижний индекс "_{}", а "." на "^{}", что оказалось очень удобным. Для написания точки и запятой без замены достаточно перед ними поставить отступ. Чтобы выйти из режима письма в индексе, нужно нажать tab.

### Для не англоязычный писателей

Если вы неанглоязычный писатель, то одна из трудностей - переключение раскладки при вхождении и выходе из математического режима. Для Windows решение данной проблемы было реализовано при помощи Powershell. Когда вы ставите пробел, точку или запятую после открывающих или закрывающих математических скобок, раскладка переключается автоматически. Правда, уже готовая комбинация для переключения раскладки соответствует ctrl (SendKeys('^')) (установил при помощи Punto Switcher). Если вам нужна другая комбинация смены, вам придется установить самому.

### Рисование

Было реализовано при помощи mspaint. Чтобы быстро открыть программу, наберите img (или \img, не забыв после нажать на escape, чтобы mspaint не запускался каждый раз при вводе символа).

### Остальное

С остальным вы можете ознакомиться сами и настроить так, как вам угодно. Для этого вам пригодится знание regex, как устроены сниппеты hypersnips и минимум js.