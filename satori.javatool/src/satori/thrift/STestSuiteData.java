package satori.thrift;

import static satori.thrift.SAttributeData.addLocalAttrMap;
import static satori.thrift.SAttributeData.convertAttrMap;
import static satori.thrift.SGlobalData.getAccumulators;
import static satori.thrift.SGlobalData.getDispatchers;
import static satori.thrift.SGlobalData.getReporters;
import static satori.thrift.STestData.createTestList;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringTokenizer;

import satori.common.SAssert;
import satori.common.SException;
import satori.common.SIdReader;
import satori.common.SPair;
import satori.metadata.SInputMetadata;
import satori.metadata.SParametersMetadata;
import satori.metadata.SParametersParser;
import satori.problem.STestSuiteBasicReader;
import satori.problem.STestSuiteReader;
import satori.session.SSession;
import satori.test.STestBasicReader;
import satori.thrift.gen.AnonymousAttribute;
import satori.thrift.gen.TestStruct;
import satori.thrift.gen.TestSuite;
import satori.thrift.gen.TestSuiteStruct;

public class STestSuiteData {
	static class TestSuiteBasicWrap implements STestSuiteBasicReader {
		private TestSuiteStruct struct;
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

	private static SParametersMetadata parseDispatcher(String str, Map<String, String> map) throws SException {
		if (str.isEmpty()) return null;
		if (!map.containsKey(str)) throw new SException("Incorrect dispatcher: " + str);
		return SParametersParser.parseParameters(str, map.get(str));
	}
	private static List<SParametersMetadata> parseAccumulators(String str, Map<String, String> map) throws SException {
		List<SParametersMetadata> result = new ArrayList<SParametersMetadata>();
		StringTokenizer tokenizer = new StringTokenizer(str, ",");
		while (tokenizer.hasMoreTokens()) {
			String token = tokenizer.nextToken();
			if (!map.containsKey(token)) throw new SException("Incorrect accumulator: " + token);
			result.add(SParametersParser.parseParameters(token, map.get(token)));
		}
		return Collections.unmodifiableList(result);
	}
	private static SParametersMetadata parseReporter(String str, Map<String, String> map) throws SException {
		if (str.isEmpty()) return null;
		if (!map.containsKey(str)) throw new SException("Incorrect reporter: " + str);
		return SParametersParser.parseParameters(str, map.get(str));
	}
	private static class LoadCommand implements SThriftCommand {
		private final long id;
		private TestSuiteStruct struct;
		private List<TestStruct> tests;
		private Map<String, AnonymousAttribute> params;
		public TestSuiteStruct getStruct() { return struct; }
		public List<TestStruct> getTests() { return tests; }
		public Map<String, AnonymousAttribute> getParameters() { return params; }
		public LoadCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			TestSuite.Iface iface = new TestSuite.Client(SThriftClient.getProtocol());
			struct = iface.TestSuite_get_struct(SSession.getToken(), id);
			tests = iface.TestSuite_get_tests(SSession.getToken(), id);
			params = iface.TestSuite_params_get_map(SSession.getToken(), id);
		}
	}
	public static STestSuiteReader load(long id) throws SException {
		LoadCommand command = new LoadCommand(id);
		SThriftClient.call(command);
		TestSuiteWrap result = new TestSuiteWrap(command.getStruct());
		result.setTests(createTestList(command.getTests()));
		SParametersMetadata dispatcher = parseDispatcher(command.getStruct().getDispatcher(), getDispatchers());
		List<SParametersMetadata> accumulators = parseAccumulators(command.getStruct().getAccumulators(), getAccumulators());
		SParametersMetadata reporter = parseReporter(command.getStruct().getReporter(), getReporters());
		result.setDispatcher(dispatcher);
		result.setAccumulators(accumulators);
		result.setReporter(reporter);
		Map<SInputMetadata, Object> general_params = new HashMap<SInputMetadata, Object>();
		if (dispatcher != null) addLocalAttrMap(dispatcher.getName() + ".", dispatcher.getGeneralParameters(), command.getParameters(), general_params);
		for (SParametersMetadata accumulator : accumulators) addLocalAttrMap(accumulator.getName() + ".", accumulator.getGeneralParameters(), command.getParameters(), general_params);
		if (reporter != null) addLocalAttrMap(reporter.getName() + ".", reporter.getGeneralParameters(), command.getParameters(), general_params);
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
	private static Map<String, AnonymousAttribute> createParams(STestSuiteReader suite) throws SException {
		Map<SInputMetadata, Object> params = suite.getGeneralParameters();
		Map<String, Object> map = new HashMap<String, Object>();
		if (suite.getDispatcher() != null) {
			String prefix = suite.getDispatcher().getName() + ".";
			for (SInputMetadata im : suite.getDispatcher().getGeneralParameters()) map.put(prefix + im.getName(), params.get(im));
		}
		for (SParametersMetadata accumulator : suite.getAccumulators()) {
			String prefix = accumulator.getName() + ".";
			for (SInputMetadata im : accumulator.getGeneralParameters()) map.put(prefix + im.getName(), params.get(im));
		}
		if (suite.getReporter() != null) {
			String prefix = suite.getReporter().getName() + ".";
			for (SInputMetadata im : suite.getReporter().getGeneralParameters()) map.put(prefix + im.getName(), params.get(im));
		}
		return convertAttrMap(map);
	}
	private static List<Map<String, AnonymousAttribute>> createTestParams(List<? extends SIdReader> tests) {
		List<Map<String, AnonymousAttribute>> result = new ArrayList<Map<String, AnonymousAttribute>>();
		for (@SuppressWarnings("unused") SIdReader test : tests) result.add(Collections.<String, AnonymousAttribute>emptyMap());
		return result;
	}
	
	private static class CreateCommand implements SThriftCommand {
		private final TestSuiteStruct struct;
		private final Map<String, AnonymousAttribute> params;
		private final List<Long> tests;
		private final List<Map<String, AnonymousAttribute>> test_params;
		private long result;
		public long getResult() { return result; }
		public CreateCommand(TestSuiteStruct struct, Map<String, AnonymousAttribute> params, List<Long> tests, List<Map<String, AnonymousAttribute>> test_params) {
			this.struct = struct;
			this.params = params;
			this.tests = tests;
			this.test_params = test_params;
		}
		@Override public void call() throws Exception {
			TestSuite.Iface iface = new TestSuite.Client(SThriftClient.getProtocol());
			result = iface.TestSuite_create(SSession.getToken(), struct, params, tests, test_params).getId();
		}
	}
	public static long create(STestSuiteReader suite) throws SException {
		SAssert.assertNotNull(suite.getTests(), "List of tests is null");
		CreateCommand command = new CreateCommand(createStruct(suite), createParams(suite), createTestIdList(suite.getTests()), createTestParams(suite.getTests()));
		SThriftClient.call(command);
		return command.getResult();
	}
	
	private static class SaveCommand implements SThriftCommand {
		private final long id;
		private final TestSuiteStruct struct;
		private final Map<String, AnonymousAttribute> params;
		private final List<Long> tests;
		private final List<Map<String, AnonymousAttribute>> test_params;
		public SaveCommand(long id, TestSuiteStruct struct, Map<String, AnonymousAttribute> params, List<Long> tests, List<Map<String, AnonymousAttribute>> test_params) {
			this.id = id;
			this.struct = struct;
			this.params = params;
			this.tests = tests;
			this.test_params = test_params;
		}
		@Override public void call() throws Exception {
			TestSuite.Iface iface = new TestSuite.Client(SThriftClient.getProtocol());
			iface.TestSuite_modify_full(SSession.getToken(), id, struct, params, tests, test_params);
		}
	}
	public static void save(STestSuiteReader suite) throws SException {
		SAssert.assertNotNull(suite.getTests(), "List of tests is null");
		SThriftClient.call(new SaveCommand(suite.getId(), createStruct(suite), createParams(suite), createTestIdList(suite.getTests()), createTestParams(suite.getTests())));
	}
	
	private static class DeleteCommand implements SThriftCommand {
		private final long id;
		public DeleteCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			TestSuite.Iface iface = new TestSuite.Client(SThriftClient.getProtocol());
			iface.TestSuite_delete(SSession.getToken(), id);
		}
	}
	public static void delete(long id) throws SException {
		SThriftClient.call(new DeleteCommand(id));
	}
	
	private static class ListCommand implements SThriftCommand {
		private final long problem_id;
		private List<TestSuiteStruct> list;
		public ListCommand(long problem_id) { this.problem_id = problem_id; }
		public List<TestSuiteStruct> getList() { return list; }
		@Override public void call() throws Exception {
			TestSuite.Iface iface = new TestSuite.Client(SThriftClient.getProtocol());
			TestSuiteStruct filter = new TestSuiteStruct();
			filter.setProblem(problem_id);
			list = iface.TestSuite_filter(SSession.getToken(), filter);
		}
	}
	public static List<STestSuiteBasicReader> list(long problem_id) throws SException {
		ListCommand command = new ListCommand(problem_id);
		SThriftClient.call(command);
		List<STestSuiteBasicReader> result = new ArrayList<STestSuiteBasicReader>();
		for (TestSuiteStruct struct : command.getList()) result.add(new TestSuiteBasicWrap(struct));
		return Collections.unmodifiableList(result);
	}
}
