import pytest

from pre_commit_hooks.jhu_check_closing_block_comments import (
    get_block_map_from_indexes,
    get_brace_indexes,
    read_backwards_for_name_before_parens,
    main,
)

all_with_comments = """
// A mock class.
public class MyClass {
   // A mock method.
   public void myMethod() {
     if (true) {
       System.out.println("This was true");
     }

     for (int i = 0; i < 5; i++) {
       System.out.println(i);

       if (true) {
         System.out.println("This was true");
       }
     } // end for

     int i = 0;
     while (i < 5) {
       System.out.println(i);
       i++;
     } // end while

     int day = 4;
     switch (day) {
       case 1:
         System.out.println("Monday");
         break;
     } // end switch
   } // end myMethod()
} // end class MyClass
"""

all_with_no_end_comments = """
// A mock class.
public class MyClass {
   // A mock method.
   public void myMethod() {
     if (true) {
       System.out.println("This was true");
     }

     for (int i = 0; i < 5; i++) {
       System.out.println(i);

       if (true) {
         System.out.println("This was true");
       }
     }

     int i = 0;
     while (i < 5) {
       System.out.println(i);
       i++;
     }

     int day = 4;
     switch (day) {
       case 1:
         System.out.println("Monday");
         break;
     }
   }
}
"""

class_with_comments = """
public class MyClass {
} // end class MyClass
"""

class_extends_with_comments = """
public class MyClass extends OtherClass {
} // end class MyClass
"""

class_with_no_end_comments = """
public class MyClass {
}
"""

method_with_comments = """
public class Original {
   public static void main(String[] args) {} // end main()
} // end class Original
"""

if_with_no_comments = """
class MyClass {
   public void checkValid() throws Exception {
      if (true) {
         throw new Exception();
      }
   } // end checkValid()
} // end class MyClass
"""

array_with_no_comments = """
public class MorseTest extends TestCase {
   public void testToEnglishSos() {
      String[] args =
      {
         "english", "... --- ... | ... --- ..."
      };
   } // end testToEnglishSos()
} // end MorseTest
"""

try_with_no_comments = """
class MyClass {
   public void checkValid() throws Exception {
      try {
         address.checkValid();
         return address;
      } catch (Exception ex) {
         System.out.printf("\tInvalid address: %s\n", ex.getMessage());
      }
   } // end checkValid()
} // end class MyClass
"""

@pytest.mark.parametrize(
    ('input_s', 'expected'),
    (
        (class_with_no_end_comments, class_with_comments),
        (class_with_comments, class_with_comments),
        (class_extends_with_comments, class_extends_with_comments),
        (method_with_comments, method_with_comments),
        (if_with_no_comments, if_with_no_comments),
        (array_with_no_comments, array_with_no_comments),
        (all_with_no_end_comments, all_with_comments),
        (try_with_no_comments, try_with_no_comments),
    ),
)
def test_fixes_missing_comments(input_s, expected, tmpdir):
    path = tmpdir.join('file.java')
    path.write(input_s)
    assert main((str(path),)) == int(input_s != expected)
    assert path.read() == expected, path.read()


@pytest.mark.parametrize(
    ('input_s', 'expected'),
    (
        ("{}", [(0, 1)]),
        ("{{}}", [(0, 3), (1, 2)]),
        (if_with_no_comments, [(15, 147), (62, 125), (80, 120)]),
        (all_with_comments,  [
            (39, 570),  # class
            (88, 550),  # method
            (105, 156), # if
            (192, 304), # for
            (242, 297), # if
            (353, 402), # while
            (454, 531), # switch
        ]),
    ),
)
def test_get_brace_indexes(input_s, expected):
    assert get_brace_indexes(input_s) == expected


@pytest.mark.parametrize(
    ('input_s', 'expected'),
    (
        ("public class MyClass {}", {(21, 22): 'CLASS'}),
        ("public static void main(String[] args) {}", {(39, 40): 'METHOD'}),
        (all_with_comments,
            {
                (39, 570): 'CLASS',
                (88, 550): 'METHOD',
                (105, 156): 'IF',
                (192, 304): 'FOR',
                (242, 297): 'IF',
                (353, 402): 'WHILE',
                (454, 531): 'SWITCH',
            },
        ),
    ),
)
def test_get_block_map(input_s, expected):
    indexes = get_brace_indexes(input_s)
    block_map = get_block_map_from_indexes(input_s, indexes)
    assert block_map == expected


@pytest.mark.parametrize(
    ('input_s', 'expected'),
    (
        ("public myMethod() {}", 'myMethod'),
        ("public static void main(String[] args) {}", 'main'),
    ),
)
def test_read_backwards_for_name_before_parens(input_s, expected):
    assert read_backwards_for_name_before_parens(input_s, input_s.index('{')) == expected
