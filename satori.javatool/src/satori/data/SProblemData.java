package satori.data;

import java.util.AbstractList;
import java.util.List;

import satori.problem.SProblemReader;
import satori.session.SSession;
import satori.task.STaskHandler;
import satori.thrift.gen.Problem;
import satori.thrift.gen.ProblemStruct;

public class SProblemData {
	static class ProblemWrap implements SProblemReader {
		private final ProblemStruct struct;
		public ProblemWrap(ProblemStruct struct) { this.struct = struct; }
		@Override public boolean hasId() { return true; }
		@Override public long getId() { return struct.getId(); }
		@Override public String getName() { return struct.getName(); }
		@Override public String getDescription() { return struct.getDescription(); }
	}
	static class ProblemListWrap extends AbstractList<SProblemReader> {
		private final List<ProblemStruct> list;
		public ProblemListWrap(List<ProblemStruct> list) { this.list = list; }
		@Override public int size() { return list.size(); }
		@Override public SProblemReader get(int index) { return new ProblemWrap(list.get(index)); }
	}
	
	public static SProblemReader load(STaskHandler handler, long id) throws Exception {
		handler.log("Loading problem...");
		Problem.Iface iface = new Problem.Client(handler.getProtocol());
		return new ProblemWrap(iface.Problem_get_struct(SSession.getToken(), id));
	}
	
	private static ProblemStruct createStruct(SProblemReader problem) {
		ProblemStruct struct = new ProblemStruct();
		struct.setName(problem.getName());
		struct.setDescription(problem.getDescription());
		return struct;
	}
	
	public static long create(STaskHandler handler, SProblemReader problem) throws Exception {
		handler.log("Creating problem...");
		Problem.Iface iface = new Problem.Client(handler.getProtocol());
		return iface.Problem_create(SSession.getToken(), createStruct(problem)).getId();
	}
	public static void save(STaskHandler handler, SProblemReader problem) throws Exception {
		handler.log("Saving problem...");
		Problem.Iface iface = new Problem.Client(handler.getProtocol());
		iface.Problem_modify(SSession.getToken(), problem.getId(), createStruct(problem));
	}
	public static void delete(STaskHandler handler, long id) throws Exception {
		handler.log("Deleting problem...");
		Problem.Iface iface = new Problem.Client(handler.getProtocol());
		iface.Problem_delete(SSession.getToken(), id);
	}
	public static List<SProblemReader> list(STaskHandler handler) throws Exception {
		handler.log("Loading problem list...");
		Problem.Iface iface = new Problem.Client(handler.getProtocol());
		ProblemStruct filter = new ProblemStruct();
		return new ProblemListWrap(iface.Problem_filter(SSession.getToken(), filter));
	}
}
