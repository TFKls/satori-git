package satori.main;

import javax.swing.InputMap;
import javax.swing.KeyStroke;
import javax.swing.SwingUtilities;
import javax.swing.UIManager;

public class SatoriTool {
	public static void main(String[] args) {
		SwingUtilities.invokeLater(new Runnable() {
			@Override public void run() {
				InputMap im = (InputMap)UIManager.get("Button.focusInputMap");
				im.put(KeyStroke.getKeyStroke("ENTER"), "pressed");
				im.put(KeyStroke.getKeyStroke("released ENTER"), "released");
				SFrame.get().start();
			}
		});
	}
}
