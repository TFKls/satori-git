package satori.problem.ui;

import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;
import java.util.List;

import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;
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
	
	private JPanel pane;
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
	
	private void initialize() {
		pane = new JPanel(new GridBagLayout());
		GridBagConstraints c = new GridBagConstraints();
		c.gridx = 0; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 0.0; c.weighty = 0.0;
		pane.add(new JLabel("Name: "), c);
		pane.add(new JLabel("Description: "), c);
		c.gridx = 1; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 0.5; c.weighty = 0.0;
		name_field = new JTextField();
		name_field.setPreferredSize(new Dimension(250, 20));
		name_field.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { updateName(); }
		});
		name_field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { updateName(); }
		});
		pane.add(name_field, c);
		desc_field = new JTextField();
		desc_field.setPreferredSize(new Dimension(250, 20));
		desc_field.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { updateDescription(); }
		});
		desc_field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { updateDescription(); }
		});
		pane.add(desc_field, c);
		c.gridx = 2; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 0.0; c.weighty = 0.0;
		pane.add(new JLabel("Dispatcher: "), c);
		pane.add(new JLabel("Accumulators: "), c);
		pane.add(new JLabel("Reporter: "), c);
		c.gridx = 3; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 0.5; c.weighty = 0.0;
		dispatchers = new SGlobalSelectionPane(new SGlobalSelectionPane.Loader() {
			@Override public List<SPair<String, String>> get() throws SException {
				return SGlobalData.convertToList(SGlobalData.getDispatchers());
			}
		}, false, new SListener0() {
			@Override public void call() { updateDispatchers(); }
		});
		dispatchers.setDimension(new Dimension(250, 20));
		pane.add(dispatchers.getPane(), c);
		accumulators = new SGlobalSelectionPane(new SGlobalSelectionPane.Loader() {
			@Override public List<SPair<String, String>> get() throws SException {
				return SGlobalData.convertToList(SGlobalData.getAccumulators());
			}
		}, true, new SListener0() {
			@Override public void call() { updateAccumulators(); }
		});
		accumulators.setDimension(new Dimension(250, 20));
		pane.add(accumulators.getPane(), c);
		reporters = new SGlobalSelectionPane(new SGlobalSelectionPane.Loader() {
			@Override public List<SPair<String, String>> get() throws SException {
				return SGlobalData.convertToList(SGlobalData.getReporters());
			}
		}, false, new SListener0() {
			@Override public void call() { updateReporters(); }
		});
		reporters.setDimension(new Dimension(250, 20));
		pane.add(reporters.getPane(), c);
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
