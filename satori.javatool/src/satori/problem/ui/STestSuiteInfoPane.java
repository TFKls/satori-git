package satori.problem.ui;

import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;
import java.util.List;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JTextField;

import satori.common.SException;
import satori.common.SListener0;
import satori.common.SPair;
import satori.common.SView;
import satori.common.ui.SGlobalSelectionPane;
import satori.common.ui.SPane;
import satori.problem.impl.STestSuiteImpl;
import satori.thrift.SGlobalData;

public class STestSuiteInfoPane implements SPane, SView {
	private final STestSuiteImpl suite;
	
	private JComponent pane;
	private JTextField name_field;
	private JTextField desc_field;
	private SGlobalSelectionPane dispatchers, accumulators, reporters;
	
	public STestSuiteInfoPane(STestSuiteImpl suite) {
		this.suite = suite;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void updateName() { suite.setName(name_field.getText()); }
	private void updateDescription() { suite.setDescription(desc_field.getText()); }
	private void updateDispatchers() { suite.setDispatchers(dispatchers.getSelection()); }
	private void updateAccumulators() { suite.setAccumulators(accumulators.getSelection()); }
	private void updateReporters() { suite.setReporters(reporters.getSelection()); }
	
	private static JComponent setLabelSizes(JComponent comp) {
		Dimension dim = new Dimension(100, 20);
		comp.setPreferredSize(dim);
		comp.setMinimumSize(dim);
		comp.setMaximumSize(dim);
		return comp;
	}
	private void initialize() {
		pane = new Box(BoxLayout.X_AXIS);
		Box pane1 = new Box(BoxLayout.Y_AXIS);
		Box pane2 = new Box(BoxLayout.Y_AXIS);
		pane1.add(setLabelSizes(new JLabel("Name")));
		pane1.add(setLabelSizes(new JLabel("Description")));
		pane1.add(setLabelSizes(new JLabel("Dispatcher")));
		pane1.add(setLabelSizes(new JLabel("Accumulators")));
		pane1.add(setLabelSizes(new JLabel("Reporter")));
		pane1.add(Box.createVerticalGlue());
		name_field = new JTextField();
		name_field.setPreferredSize(new Dimension(480, 20));
		name_field.setMinimumSize(new Dimension(480, 20));
		name_field.setMaximumSize(new Dimension(480, 20));
		name_field.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { updateName(); }
		});
		name_field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { updateName(); }
		});
		pane2.add(name_field);
		desc_field = new JTextField();
		desc_field.setPreferredSize(new Dimension(480, 20));
		desc_field.setMinimumSize(new Dimension(480, 20));
		desc_field.setMaximumSize(new Dimension(480, 20));
		desc_field.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { updateDescription(); }
		});
		desc_field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { updateDescription(); }
		});
		pane2.add(desc_field);
		dispatchers = new SGlobalSelectionPane(new SGlobalSelectionPane.Loader() {
			@Override public List<SPair<String, String>> get() throws SException {
				return SGlobalData.convertToList(SGlobalData.getDispatchers());
			}
		}, false, new SListener0() {
			@Override public void call() { updateDispatchers(); }
		});
		dispatchers.getPane().setPreferredSize(new Dimension(480, 20));
		dispatchers.getPane().setMinimumSize(new Dimension(480, 20));
		dispatchers.getPane().setMaximumSize(new Dimension(480, 20));
		pane2.add(dispatchers.getPane());
		accumulators = new SGlobalSelectionPane(new SGlobalSelectionPane.Loader() {
			@Override public List<SPair<String, String>> get() throws SException {
				return SGlobalData.convertToList(SGlobalData.getAccumulators());
			}
		}, true, new SListener0() {
			@Override public void call() { updateAccumulators(); }
		});
		accumulators.getPane().setPreferredSize(new Dimension(480, 20));
		accumulators.getPane().setMinimumSize(new Dimension(480, 20));
		accumulators.getPane().setMaximumSize(new Dimension(480, 20));
		pane2.add(accumulators.getPane());
		reporters = new SGlobalSelectionPane(new SGlobalSelectionPane.Loader() {
			@Override public List<SPair<String, String>> get() throws SException {
				return SGlobalData.convertToList(SGlobalData.getReporters());
			}
		}, false, new SListener0() {
			@Override public void call() { updateReporters(); }
		});
		reporters.getPane().setPreferredSize(new Dimension(480, 20));
		reporters.getPane().setMinimumSize(new Dimension(480, 20));
		reporters.getPane().setMaximumSize(new Dimension(480, 20));
		pane2.add(reporters.getPane());
		pane2.add(Box.createVerticalGlue());
		pane.add(pane1);
		pane.add(Box.createHorizontalStrut(5));
		pane.add(pane2);
		pane.add(Box.createHorizontalGlue());
		update();
	}
	
	@Override public void update() {
		name_field.setText(suite.getName());
		desc_field.setText(suite.getDescription());
		dispatchers.setSelection(suite.getDispatchers());
		accumulators.setSelection(suite.getAccumulators());
		reporters.setSelection(suite.getReporters());
	}
}
