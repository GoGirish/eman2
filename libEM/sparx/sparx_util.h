#ifndef sparx_util_h
#define sparx_util_h
#include <cstddef>

/** @file util.h
 *  utilities of image proccessing -- 
 *  @author P. A. Penczek <Pawel.A.Penczek@uth.tmc.edu>.
 *  The University of Texas.
 *  Please do not modify the contents of this document
 *  without written consent of the author.
 *
 *  @date $Date: 2006/04/03
 *
 *  
 *  
 *
 */
 namespace EMAN
{
	class EMData;
	
	class SparxUtil
	{
	public:
		struct Peak {
	    	float val;
	    	float xpos;
		    float ypos;
	    	float zpos;
	    	Peak (float val_, float xpos_=0, float ypos_=0, float zpos_=0)
	        : val(val_), xpos(xpos_), ypos(ypos_), zpos(zpos_) {}
		};
		
		/** Search specified number peaks in 1D, 2D, or 3D real images.
	  	* and output the peaks in descendent order */
	  	static vector<Peak> peak_search(EMData* img, int ml, float invert);
	  	
	private:
		bool peakcmp(const Peak p1, const Peak p2);  		
	};
	
}	 

#endif	//sparx_util_h
