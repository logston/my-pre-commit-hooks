import pytest

from pre_commit_hooks.jhu_check_closing_block_comments import main
from pre_commit_hooks.jhu_check_closing_block_comments import get_depth_map
from pre_commit_hooks.jhu_check_closing_block_comments import get_block_map_from_depth_map

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

@pytest.mark.parametrize(
    ('input_s', 'expected'),
    (
        (class_with_no_end_comments, class_with_comments),
        (class_with_comments, class_with_comments),
        (class_extends_with_comments, class_extends_with_comments),
        (method_with_comments, method_with_comments),
        (if_with_no_comments, if_with_no_comments),
        (array_with_no_comments, array_with_no_comments),
    ),
)
def test_fixes_missing_comments(input_s, expected, tmpdir):
    path = tmpdir.join('file.java')
    path.write(input_s)
    assert main((str(path),)) == int(input_s != expected)
    assert path.read() == expected, path.read()


def test_get_depth_map():
    content = """
class MyClass {
   public void checkValid() throws Exception {
      if (true) {
         throw new Exception();
      }
   } // end checkValid()
} // end class MyClass
"""
    depth_map = get_depth_map(content)
    assert depth_map == {
        0: {'end': 22, 'start': 154},
        1: {'end': 44, 'start': 107},
        2: {'end': 49, 'start': 89}
    }


def test_get_block_map():
    content = """
class MyClass {
   public void checkValid() throws Exception {
      if (true) {
         throw new Exception();
      }
   } // end checkValid()
} // end class MyClass
"""
    depth_map = get_depth_map(content)
    block_map = get_block_map_from_depth_map(content, depth_map)
    assert block_map == {
        (16, 148): 'CLASS',
        (63, 126): 'METHOD',
    }
