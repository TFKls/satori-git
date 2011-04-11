package satori.data;

import static satori.data.SAttributeData.convertAnonymousAttribute;
import static satori.data.SAttributeData.createAnonymousAttribute;
import static satori.data.SGlobalData.getAccumulators;
import static satori.data.SGlobalData.getDispatchers;
import static satori.data.SGlobalData.getReporters;

import java.util.AbstractList;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringTokenizer;

import satori.common.SAssert;
import satori.common.SIdReader;
import satori.common.SPair;
import satori.data.STestData.TestListWrap;
import satori.metadata.SInputMetadata;
import satori.metadata.SParametersMetadata;
import satori.metadata.SParametersParser;
import satori.problem.STestSuiteBasicReader;
import satori.problem.STestSuiteReader;
import satori.session.SSession;
import satori.task.STaskManager;
import satori.test.STestBasicReader;
import satori.thrift.gen.AnonymousAttribute;
import satori.thrift.gen.TestSuite;
import satori.thrift.gen.TestSuiteStruct;

public class STestSuiteData {
	static class TestSuiteBasicWrap implements STestSuiteBasicReader {
		private final TestSuiteStruct struct;
		public TestSuiteBasicWrap(TestSuiteStruct struct) { this.struct = struct; }
		@Override public boolean hasId() { return true; }
		@Override public long getId() { return struct.getId(); }
		@Override public long getProblemId() { return struct.getProblem(); }
		@Override public String getName() { return struct.getName(); }
		@Override public String getDescription() { return struct.getDescription(); }
	}
	static class TestSuiteWrap extends TestSuiteBasicWrap implements STestSuiteReader {
		private List<STestBasicReader> tests;
		private SParametersMetadata dispatcher;
		private List<SParametersMetadata> accumulators;
		private SParametersMetadata reporter;
		private Map<SInputMetadata, Object> general_params;
		private Map<SPair<SInputMetadata, Long>, Object> test_params;
		public TestSuiteWrap(TestSuiteStruct struct) { super(struct); }
		public void setTests(List<STestBasicReader> tests) { this.tests = tests; }
		public void setDispatcher(SParametersMetadata dispatcher) { this.dispatcher = dispatcher; }
		public void setAccumulators(List<SParametersMetadata> accumulators) { this.accumulators = accumulators; }
		public void setReporter(SParametersMetadata reporter) { this.reporter = reporter; }
		public void setGeneralParameters(Map<SInputMetadata, Object> general_params) { this.general_params = general_params; }
		public void setTestParameters(Map<SPair<SInputMetadata, Long>, Object> test_params) { this.test_params = test_params; }
		@Override public List<STestBasicReader> getTests() { return tests; }
		@Override public SParametersMetadata getDispatcher() { return dispatcher; }
		@Override public List<SParametersMetadata> getAccumulators() { return accumulators; }
		@Override public SParametersMetadata getReporter() { return reporter; }
		@Override public Map<SInputMetadata, Object> getGeneralParameters() { return general_params; }
		@Override public Map<SPair<SInputMetadata, Long>, Object> getTestParameters() { return test_params; }
	}
	static class TestSuiteListWrap extends AbstractList<STestSuiteBasicReader> {
		private final List<TestSuiteStruct> list;
		public TestSuiteListWrap(List<TestSuiteStruct> list) { this.list = list; }
		@Override public int size() { return list.size(); }
		@Override public STestSuiteBasicReader get(int index) { return new TestSuiteBasicWrap(list.get(index)); }
	}
	
	private static void fillAnonymousAttributes(String prefix, List<SInputMetadata> meta_list, Map<SInputMetadata, Object> params, Map<String, AnonymousAttribute> result) {
		for (SInputMetadata meta : meta_list) {
			Object param = params.get(meta);
			if (param != null) result.put(prefix + "." + meta.getName(), createAnonymousAttribute(param));
		}
	}
	private static void fillParameters(String prefix, List<SInputMetadata> meta_list, Map<String, AnonymousAttribute> attrs, Map<SInputMetadata, Object> result) {
		for (SInputMetadata meta : meta_list) {
			AnonymousAttribute attr = attrs.get(prefix + "." + meta.getName());
			if (attr != null) result.put(meta, convertAnonymousAttribute(attr));
		}
	}
	
	private static SParametersMetadata parseDispatcher(String str, Map<String, String> map) throws Exception {
		if (str.isEmpty()) return null;
		if (!map.containsKey(str)) throw new Exception("Incorrect dispatcher: " + str);
		return SParametersParser.parseParametersTask(str, map.get(str));
	}
	private static List<SParametersMetadata> parseAccumulators(String str, Map<String, String> map) throws Exception {
		List<SParametersMetadata> result = new ArrayList<SParametersMetadata>();
		StringTokenizer tokenizer = new StringTokenizer(str, ",");
		while (tokenizer.hasMoreTokens()) {
			String token = tokenizer.nextToken();
			if (!map.containsKey(token)) throw new Exception("Incorrect accumulator: " + token);
			result.add(SParametersParser.parseParametersTask(token, map.get(token)));
		}
		return Collections.unmodifiableList(result);
	}
	private static SParametersMetadata parseReporter(String str, Map<String, String> map) throws Exception {
		if (str.isEmpty()) return null;
		if (!map.containsKey(str)) throw new Exception("Incorrect reporter: " + str);
		return SParametersParser.parseParametersTask(str, map.get(str));
	}
	public static STestSuiteReader load(long id) throws Exception {
		STaskManager.log("Loading test suite...");
		TestSuite.Iface iface = new TestSuite.Client(SSession.getProtocol());
		TestSuiteStruct struct = iface.TestSuite_get_struct(SSession.getToken(), id);
		TestSuiteWrap result = new TestSuiteWrap(struct);
		result.setTests(new TestListWrap(iface.TestSuite_get_tests(SSession.getToken(), id)));
		SParametersMetadata dispatcher = parseDispatcher(struct.getDispatcher(), getDispatchers());
		List<SParametersMetadata> accumulators = parseAccumulators(struct.getAccumulators(), getAccumulators());
		SParametersMetadata reporter = parseReporter(struct.getReporter(), getReporters());
		result.setDispatcher(dispatcher);
		result.setAccumulators(accumulators);
		result.setReporter(reporter);
		Map<String, AnonymousAttribute> params = iface.TestSuite_params_get_map(SSession.getToken(), id);
		Map<SInputMetadata, Object> general_params = new HashMap<SInputMetadata, Object>();
		if (dispatcher != null) fillParameters(dispatcher.getName(), dispatcher.getGeneralParameters(), params, general_params);
		for (SParametersMetadata accumulator : accumulators) fillParameters(accumulator.getName(), accumulator.getGeneralParameters(), params, general_params);
		if (reporter != null) fillParameters(reporter.getName(), reporter.getGeneralParameters(), params, general_params);
		result.setGeneralParameters(general_params);
		result.setTestParameters(Collections.<SPair<SInputMetadata, Long>, Object>emptyMap());
		return result;
	}
	
	private static String parseList(List<SParametersMetadata> params) {
		StringBuilder result = null;
		for (SParametersMetadata p : params) {
			if (result != null) result.append(",");
			else result = new StringBuilder();
			result.append(p.getName());
		}
		return result != null ? result.toString() : "";
	}
	private static TestSuiteStruct createStruct(STestSuiteReader suite) {
		TestSuiteStruct struct = new TestSuiteStruct();
		struct.setProblem(suite.getProblemId());
		struct.setName(suite.getName());
		struct.setDescription(suite.getDescription());
		struct.setDispatcher(suite.getDispatcher() != null ? suite.getDispatcher().getName() : "");
		struct.setAccumulators(parseList(suite.getAccumulators()));
		struct.setReporter(suite.getReporter() != null ? suite.getReporter().getName() : "");
		return struct;
	}
	private static List<Long> createTestIdList(List<? extends SIdReader> tests) {
		List<Long> list = new ArrayList<Long>();
		for (SIdReader test : tests) list.add(test.getId());
		return list;
	}
	private static Map<String, AnonymousAttribute> createParams(STestSuiteReader suite) {
		Map<SInputMetadata, Object> params = suite.getGeneralParameters();
		Map<String, AnonymousAttribute> result = new HashMap<String, AnonymousAttribute>();
		if (suite.getDispatcher() != null) fillAnonymousAttributes(suite.getDispatcher().getName(), suite.getDispatcher().getGeneralParameters(), params, result);
		for (SParametersMetadata accumulator : suite.getAccumulators()) fillAnonymousAttributes(accumulator.getName(), accumulator.getGeneralParameters(), params, result);
		if (suite.getReporter() != null) fillAnonymousAttributes(suite.getReporter().getName(), suite.getReporter().getGeneralParameters(), params, result);
		return result;
	}
	private static List<Map<String, AnonymousAttribute>> createTestParams(List<? extends SIdReader> tests) {
		List<Map<String, AnonymousAttribute>> result = new ArrayList<Map<String, AnonymousAttribute>>();
		for (@SuppressWarnings("unused") SIdReader test : tests) result.add(Collections.<String, AnonymousAttribute>emptyMap());
		return result;
	}
	
	public static long create(STestSuiteReader suite) throws Exception {
		SAssert.assertNotNull(suite.getTests(), "List of tests is null");
		STaskManager.log("Creating test suite...");
		TestSuite.Iface iface = new TestSuite.Client(SSession.getProtocol());
		return iface.TestSuite_create(SSession.getToken(), createStruct(suite), createParams(suite), createTestIdList(suite.getTests()), createTestParams(suite.getTests())).getId();
	}
	public static void save(STestSuiteReader suite) throws Exception {
		SAssert.assertNotNull(suite.getTests(), "List of tests is null");
		STaskManager.log("Saving test suite...");
		TestSuite.Iface iface = new TestSuite.Client(SSession.getProtocol());
		iface.TestSuite_modify_full(SSession.getToken(), suite.getId(), createStruct(suite), createParams(suite), createTestIdList(suite.getTests()), createTestParams(suite.getTests()));
	}
	public static void delete(long id) throws Exception {
		STaskManager.log("Deleting test suite...");
		TestSuite.Iface iface = new TestSuite.Client(SSession.getProtocol());
		iface.TestSuite_delete(SSession.getToken(), id);
	}
	public static List<STestSuiteBasicReader> list(long problem_id) throws Exception {
		STaskManager.log("Loading test suite list...");
		TestSuite.Iface iface = new TestSuite.Client(SSession.getProtocol());
		TestSuiteStruct filter = new TestSuiteStruct();
		filter.setProblem(problem_id);
		return new TestSuiteListWrap(iface.TestSuite_filter(SSession.getToken(), filter));
	}
}
