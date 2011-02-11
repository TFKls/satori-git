package satori.test.ui;

import javax.swing.Icon;
import javax.swing.ImageIcon;

public class SIcons {
	public static Icon moveIcon;
	public static Icon saveIcon;
	public static Icon refreshIcon;
	public static Icon trashIcon;
	public static Icon removeIcon;
	public static Icon addIcon;
	public static Icon runIcon;
	
	public static void loadResources(ClassLoader loader) {
		moveIcon = new ImageIcon(loader.getResource("icons/move.gif"));
		saveIcon = new ImageIcon(loader.getResource("icons/save.gif"));
		refreshIcon = new ImageIcon(loader.getResource("icons/refresh.gif"));
		trashIcon = new ImageIcon(loader.getResource("icons/trash.gif"));
		removeIcon = new ImageIcon(loader.getResource("icons/remove.gif"));
		addIcon = new ImageIcon(loader.getResource("icons/add.gif"));
		runIcon = new ImageIcon(loader.getResource("icons/run.gif"));
	}
}
