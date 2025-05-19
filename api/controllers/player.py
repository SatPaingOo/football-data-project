### Player routes ###
from flask import jsonify, request
from football import get_players

def get_players_list():
    """API endpoint to get players with pagination and sorting"""
    try:
        # Get query parameters with defaults
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('pageSize', default=10, type=int)
        sort_column = request.args.get('sortColumn', default='id', type=str)
        sort_order = request.args.get('sortOrder', default='asc', type=str)
        
        # Validate parameters
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:  # Limit maximum page size
            page_size = 100
            
        # Get paginated players directly from database
        result, total_records = get_players(
            page=page, 
            page_size=page_size, 
            sort_column=sort_column, 
            sort_order=sort_order
        )
        
        # Calculate total pages
        total_pages = (total_records + page_size - 1) // page_size  # Ceiling division
        
        # Convert DataFrame to a list of dictionaries for JSON serialization
        players_list = result.to_dict(orient='records')
        
        # Prepare pagination metadata
        pagination = {
            "page": page,
            "pageSize": page_size,
            "totalRecords": total_records,
            "totalPages": total_pages,
            "sortColumn": sort_column,
            "sortOrder": sort_order
        }
        
        return jsonify({ 
            "result": True, 
            "data": players_list,
            "pagination": pagination,
            "status": "success", 
            "message": "Players retrieved successfully"
        })
    except Exception as e:
        return jsonify({
            "result": False,
            "status": "error", 
            "message": str(e)
        }), 500