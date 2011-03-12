package satori.main;

import javax.swing.InputMap;
import javax.swing.KeyStroke;
import javax.swing.SwingUtilities;
import javax.swing.UIManager;

import satori.test.ui.SIcons;

public class SatoriTool {
	public static void main(String[] args) {
		SIcons.loadResources(SatoriTool.class.getClassLoader());
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
